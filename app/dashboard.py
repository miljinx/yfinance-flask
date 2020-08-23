from datetime import datetime

import tempfile

import humanize

from flask import (
    Blueprint,
    flash,
    get_flashed_messages,
    g,
    session,
    redirect,
    render_template,
    request,
    url_for,
    send_file)

import yfinance as yf

bp = Blueprint('dashboard', __name__)

DOWNLOAD_INTERVAL_SECONDS = 10

PERIOD_OPTIONS = (
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

INTERVAL_OPTIONS = (
    ('1d', '1 day'),
    ('5d', '5 days'),
    ('1wk', '1 week'),
    ('1mo', '1 month'),
    ('3mo', '3 months'),
)

@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        ticker_symbol = request.form['ticker_symbol']
        retrieved_ticker_symbol = None
        try:
            yf_ticker = yf.Ticker(ticker_symbol)
            retrieved_ticker_symbol = yf_ticker.info['symbol']
        except ValueError:
            flash(f"Ticker symbol '{ticker_symbol}' not found.")

        if retrieved_ticker_symbol:
            return redirect(
                url_for(
                    'dashboard.info',
                    ticker_symbol=retrieved_ticker_symbol))

    return render_template('dashboard/index.html')


@bp.route('/info')
def info():
    date_of_search = datetime.now().strftime('%B %-d, %Y')
    ticker_symbol = request.args.get('ticker_symbol').upper()
    # TODO cache ticker_info
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

    return render_template(
        'dashboard/info.html',
        ticker_symbol=ticker_symbol,
        date_of_search=date_of_search,
        details=details,
        period_options=PERIOD_OPTIONS,
        interval_options=INTERVAL_OPTIONS)


@bp.route('/download', methods=('POST',))
def download():
    ticker_symbol = request.form['ticker'].upper()

    if 'last_download_at' in session:
        seconds_since_last_download = int(
            (datetime.now() - session['last_download_at']).total_seconds())
        if seconds_since_last_download < DOWNLOAD_INTERVAL_SECONDS:
            flash(
                f'Please wait {seconds_since_last_download} seconds '
                f'before downloading again.')
            return redirect(url_for('dashboard.info', ticker_symbol=ticker_symbol))

    yf_ticker = yf.Ticker(ticker_symbol)
    period = request.form['period']
    interval = request.form['interval']
    ticker_history = yf_ticker.history(period=period, interval=interval)

    session['last_download_at'] = datetime.now()

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f'stock_data__{ticker_symbol}__{timestamp}.csv'
    with tempfile.NamedTemporaryFile() as file:
        ticker_history.to_csv(file.name)  # write to tempfile in csv format
        return send_file(
            file.name, mimetype='text/csv', as_attachment=True,
            attachment_filename=filename)
