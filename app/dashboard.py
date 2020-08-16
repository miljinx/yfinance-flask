from datetime import datetime

import humanize

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
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


@bp.route('/download', methods=('GET', 'POST'))
@login_required
def download():
    date_and_time = datetime.now().strftime('%B %-d, %Y at %-I:%M %p')
    ticker_symbol = request.args.get('ticker_symbol')
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
    if request.method == 'POST':
        period = request.form['period']
        interval = request.form['interval']  # only allow 1d, 5d, 1wk,1mo, 3mo
        ticker_history = yf_ticker.history(period=period, interval=interval)
        # TODO use send_file() for downloads
        # TODO remove files from disk after download completion
        # TODO validation
        log_activity(
            g.user['username'],
            f'download, {ticker_symbol}, {period}, {interval}')

    return render_template(
        'dashboard/download.html',
        date_and_time=date_and_time,
        details=details)


def log_activity(username, details):
    db = get_db()
    db.execute(
        'INSERT INTO logs(details, timestamp) VALUES (?,?)',
        (f'{username}, {details}',
         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    db.commit()
