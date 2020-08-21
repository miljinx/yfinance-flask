from datetime import datetime

import tempfile

import humanize

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)

import yfinance as yf

from app.auth import login_required
from app.db import get_db

bp = Blueprint('dashboard', __name__)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    if request.method == 'POST':
        ticker_symbol = request.form['ticker_symbol']
        log_activity(
            g.user['username'],
            f'search, {ticker_symbol}')
        retrieved_ticker_symbol = None
        try:
            yf_ticker = yf.Ticker(ticker_symbol)
            retrieved_ticker_symbol = yf_ticker.info['symbol']
        except ValueError:
            flash(f"Ticker symbol '{ticker_symbol}' not found.")

        if retrieved_ticker_symbol:
            return redirect(
                url_for(
                    'dashboard.download',
                    ticker_symbol=retrieved_ticker_symbol))

    return render_template('dashboard/index.html')


@bp.route('/info')
@login_required
def info():
    date_and_time = datetime.now().strftime('%B %-d, %Y at %-I:%M %p')
    ticker_symbol = request.args.get('ticker_symbol').upper()
    yf_ticker = yf.Ticker(ticker_symbol)
    ticker_info = yf_ticker.info
    details = {
        'name': ticker_info['longName'],
        'symbol': ticker_info['symbol'],
        'industry': ticker_info['industry'],
        'logo_url': ticker_info['logo_url'],
        'web_url': ticker_info['website'],
        'description': ticker_info['longBusinessSummary'],
        'market_cap': humanize.intword(ticker_info['marketCap'])
        if ticker_info['marketCap'] > 999999
        else humanize.intcomma(ticker_info['marketCap']),
        'open_price': humanize.intcomma(ticker_info['open']),
    }
    period_options = (
        ('1mo', '1 month'),
        ('3mo', '3 months'),
        ('6mo', '6 months'),
        ('1y', '1 year'),
        ('2y', '2 years'),
        ('5y', '5 years'),
        ('10y', '10 years'),
        ('ytd', 'Year to Date'),
        ('max', 'Max'),
    )
    interval_options = (
        ('1d', '1 day'),
        ('5d', '5 days'),
        ('1wk', '1 week'),
        ('1mo', '1 month'),
        ('3mo', '3 months'),
    )

    return render_template(
        'dashboard/download.html',
        ticker_symbol=ticker_symbol,
        date_and_time=date_and_time,
        details=details,
        period_options=period_options,
        interval_options=interval_options)


@bp.route('/download', methods=('POST',))
@login_required
def download():
    # TODO simple rate-limiting
    ticker_symbol = request.form['ticker'].upper()
    yf_ticker = yf.Ticker(ticker_symbol)
    period = request.form['period']
    interval = request.form['interval']
    ticker_history = yf_ticker.history(
        period=period, interval=interval)

    log_activity(
        g.user['username'],
        f'download, '
        f'ticker: {ticker_symbol}, '
        f'period: {period}, '
        f'interval: {interval}')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f'stock_data__{ticker_symbol}__{timestamp}.csv'
    with tempfile.NamedTemporaryFile() as file:
        ticker_history.to_csv(file.name)  # write to tempfile in csv format
        return send_file(
            file.name, mimetype='text/csv', as_attachment=True,
            attachment_filename=filename)


def log_activity(username, details):
    db = get_db()
    db.execute(
        'INSERT INTO logs(details, timestamp) VALUES (?,?)',
        (f'{username}, {details}',
         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    db.commit()
