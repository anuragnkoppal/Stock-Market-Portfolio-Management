from flask import Flask, render_template, request, session
from datetime import timedelta
import hashlib
import yaml
import pymysql

app = Flask(__name__)

with open('/Users/Anurag/Desktop/PROJECTS/Portfolio-Management-System-main 4.46.50 PM/db.yaml') as f:
    db = yaml.safe_load(f)

app.secret_key = db['secret_key']
app.permanent_session_lifetime = timedelta(minutes=10)  # Session lasts for 10 minutes

# Database configuration
# Database configuration
# Database configuration
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "anu12345",
    'db': "portfolio",
    'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'
}


conn = pymysql.connect(**db_config)
cursor = conn.cursor()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.permanent = True
        user_details = request.form

        try:
            # If not logged in case
            username = user_details['username']
            password = user_details['password']

            # Password hashing to 224 characters
            password_hashed = hashlib.sha224(password.encode()).hexdigest()
        except KeyError:
            if 'logout' in request.form and request.form['logout'] == '':
                # If logged in case (for signout form return)
                session.pop('user', None)
            return render_template('/index.html', session=session)

        try:
            # Check if the entered username and password are correct
            with conn.cursor() as cursor:
                sql = "SELECT username FROM user_profile WHERE username = %s AND user_password = %s"
                cursor.execute(sql, (username, password_hashed))
                result = cursor.fetchone()

            if result:
                # Login successful
                session['user'] = username
                return portfolio()

        except pymysql.Error as e:
            # Handle database error, log or render an error template
            print(f"Database error: {e}")

        # Login unsuccessful
        return render_template('alert2.html')

    else:
        return render_template('index.html', session=session)

@app.route('/portfolio.html')
def portfolio():
    # Check if we have logged in users
    if "user" not in session:
        return render_template('alert1.html')

    # Query for holdings
    query_holdings = '''
        SELECT f
            symbol, 
            SUM(quantity) AS quantity, 
            LTP,
            ROUND(getTotal(-SUM(quantity) * LTP), 2) AS current_value,
            capGain(
                ROUND(getTotal(-SUM(quantity) * LTP) - getTotal(SUM(quantity) * rate), 2),
                MAX(transaction_date)
            ) AS profit_loss
        FROM 
            transaction_history T
        NATURAL JOIN 
            company_price C
        WHERE 
            username = %s
        GROUP BY 
            symbol;
    '''

    with conn.cursor() as cur:
        user = [session['user']]
        cur.execute(query_holdings, user)
        holdings = cur.fetchall()

    # Query for watchlist
    query_watchlist = '''
        SELECT
            symbol,
            MAX(LTP) AS LTP,
            MAX(PC) AS PC,
            ROUND(MAX(LTP-PC), 2) AS CH,
            ROUND(MAX((LTP-PC)/PC*100), 2) AS CH_percent
        FROM watchlist
        NATURAL JOIN company_price
        WHERE username = %s
        GROUP BY symbol;
    '''
    with conn.cursor() as cur:
        cur.execute(query_watchlist, user)
        watchlist = cur.fetchall()

    # Query for stock suggestion
    query_suggestions = '''
        SELECT symbol, EPS, ROE, book_value, rsi, adx, pe_ratio, macd
        FROM company_price
        NATURAL JOIN fundamental_averaged
        NATURAL JOIN technical_signals
        NATURAL JOIN company_profile
        WHERE
        EPS > 25 AND roe > 13 AND
        book_value > 100 AND
        rsi > 50 AND adx > 23 AND
        pe_ratio < 35 AND
        macd = 'bull'
        ORDER BY symbol;
    '''
    with conn.cursor() as cur:
        cur.execute(query_suggestions)
        suggestions = cur.fetchall()

    # Query on EPS
    query_eps = '''
        SELECT symbol, ltp, eps
        FROM fundamental_averaged
        WHERE eps > 30
        ORDER BY eps;
    '''
    with conn.cursor() as cur:
        cur.execute(query_eps)
        eps = cur.fetchall()

    # Query on PE Ratio
    query_pe = '''
        SELECT symbol, ltp, pe_ratio
        FROM fundamental_averaged
        WHERE pe_ratio < 30;
    '''
    with conn.cursor() as cur:
        cur.execute(query_pe)
        pe = cur.fetchall()

    # Query on technical signals
    query_technical = '''
        SELECT *
        FROM technical_signals
        WHERE ADX > 23 AND rsi > 50 AND rsi < 70 AND MACD = 'bull';
    '''
    with conn.cursor() as cur:
        cur.execute(query_technical)
        technical = cur.fetchall()

    # Query for pie chart
    query_sectors = '''
        SELECT C.sector, sum(A.quantity*B.LTP) as current_value 
        FROM holdings_view A
        INNER JOIN company_price B ON A.symbol = B.symbol
        INNER JOIN company_profile C ON A.symbol = C.symbol
        WHERE username = %s
        GROUP BY C.sector, A.quantity, B.LTP;
    '''
    with conn.cursor() as cur:
        cur.execute(query_sectors, user)
        sectors_total = cur.fetchall()

    # Convert list to json type having percentage and label keys
    piechart_dict = toPercentage(sectors_total)
    piechart_dict[0]['type'] = 'pie'
    piechart_dict[0]['hole'] = 0.4

    # No need to close the connection, as it is a global object.

    return render_template('portfolio.html', holdings=holdings, user=user[0], suggestions=suggestions, eps=eps, pe=pe, technical=technical, watchlist=watchlist, piechart=piechart_dict)


def toPercentage(sectors_total):
    json_format = {}
    total = 0

    for row in sectors_total:
        total += row[1]

    json_format['values'] = [round((row[1]/total)*100, 2)
                             for row in sectors_total]
    json_format['labels'] = [row[0] for row in sectors_total]
    return [json_format]
    
def list_to_json(listToConvert):
    json_format = {}
    temp_dict = {}
    val_per = []
    for value in listToConvert:
        temp_dict[value] = listToConvert.count(value)

    values = [val for val in temp_dict.values()]
    for i in range(len(values)):
        per = ((values[i]/sum(values))*100)
        val_per.append(round(per, 2))
    keys = [k for k in temp_dict.keys()]
    json_format['values'] = val_per
    json_format['labels'] = keys
    return [json_format]


@app.route('/add_transaction.html', methods=['GET', 'POST'])
def add_transaction():
    # Query for all companies (for drop-down menu)
    cur = conn.cursor()
    query_companies = '''select symbol from company_profile'''
    cur.execute(query_companies)
    companies = cur.fetchall()

    if request.method == 'POST':
        transaction_details = request.form
        symbol = transaction_details['symbol']
        date = transaction_details['transaction_date']
        transaction_type = transaction_details['transaction_type']
        quantity = float(transaction_details['quantity'])
        rate = float(transaction_details['rate'])
        if transaction_type == 'Sell':
            quantity = -quantity

        cur = conn.cursor()
        query = '''insert into transaction_history(username, symbol, transaction_date, quantity, rate) values
(%s, %s, %s, %s, %s)'''
        values = [session['user'], symbol, date, quantity, rate]
        cur.execute(query, values)
        conn.commit()

    return render_template('add_transaction.html', companies=companies)

@app.route('/add_watchlist.html', methods=['GET', 'POST'])
def add_watchlist():
    # Query for companies (for drop-down menu) excluding those which are already in watchlist
    cur = conn.cursor()
    query_companies = '''SELECT symbol from company_profile
    where symbol not in
    (select symbol from watchlist
    where username = %s);
    '''
    user = [session['user']]
    cur.execute(query_companies, user)
    companies = cur.fetchall()

    if request.method == 'POST':
        watchlist_details = request.form
        symbol = watchlist_details['symbol']
        cur = conn.cursor()
        query = '''insert into watchlist(username, symbol) values
        (%s, %s)'''
        values = [session['user'], symbol]
        cur.execute(query, values)
        conn.commit()

    return render_template('add_watchlist.html', companies=companies)
@app.route('/stockprice.html')
def current_price(company='all'):
    cur = conn.cursor()
    if company == 'all':
        query = '''SELECT symbol, LTP, PC, round((LTP-PC), 2) as CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent FROM company_price
        order by symbol;
        '''
        cur.execute(query)
    else:
        company = [company]
        query = '''SELECT symbol, LTP, PC, round((LTP-PC), 2) as CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent FROM company_price
        where symbol = %s;
        '''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('stockprice.html', values=rv)


@app.route('/fundamental.html', methods=['GET'])
def fundamental_report(company='all'):
    cur = conn.cursor()
    if company == 'all':
        query = '''select * from fundamental_averaged;'''
        cur.execute(query)
    else:
        company = [company]
        query = '''select F.symbol, report_as_of, LTP, eps, roe, book_value, round(LTP/eps, 2) as pe_ratio
            from fundamental_report F
            inner join company_price C
            on F.symbol = C.symbol
            where F.symbol = %s;
        '''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('fundamental.html', values=rv)


@app.route('/technical.html')
def technical_analysis(company='all'):
    cur = conn.cursor()
    if company == 'all':
        query = '''select A.symbol, sector, LTP, volume, RSI, ADX, MACD from technical_signals A 
            left join company_profile B
            on A.symbol = B.symbol
            order by (A.symbol);
        '''
        cur.execute(query)
    else:
        company = [company]
        query = '''SELECT * FROM technical_signals where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('technical.html', values=rv)


@app.route('/companyprofile.html')
def company_profile(company='all'):
    cur = conn.cursor()
    if company == 'all':
        query = '''select * from company_profile
            order by(symbol);
        '''
        cur.execute(query)
    else:
        company = [company]
        query = '''select * from company_profile where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('companyprofile.html', values=rv)


@app.route('/dividend.html')
def dividend_history(company='all'):
    cur = conn.cursor()
    if company == 'all':
        query = '''select * from dividend_history
            order by(symbol);
        '''
        cur.execute(query)
    else:
        company = [company]
        query = '''select * from dividend_history where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('dividend.html', values=rv)


@app.route('/watchlist.html')
def watchlist():
    if 'user' not in session:
        return render_template('alert1.html')

    cur = conn.cursor()
    query_watchlist = '''
    SELECT
   symbol,
   MAX(LTP) AS LTP,
   MAX(PC) AS PC,
   ROUND(MAX(LTP-PC), 2) AS CH,
   ROUND(MAX((LTP-PC)/PC*100), 2) AS CH_percent
FROM watchlist
NATURAL JOIN company_price
WHERE username = %s
GROUP BY symbol, LTP, PC;
'''

    cur.execute(query_watchlist, [session['user']])
    watchlist = cur.fetchall()

    return render_template('watchlist.html', user=session['user'], watchlist=watchlist)
@app.route('/holdings.html')
def holdings():
    if "user" not in session:
        return render_template('alert1.html')

    cur = conn.cursor()
    query_holdings = '''select A.symbol, A.quantity, B.LTP, round(A.quantity*B.LTP, 2) as current_value from holdings_view A
        inner join company_price B
        on A.symbol = B.symbol
        where username = %s
    '''
    cur.execute(query_holdings, [session['user']])
    holdings = cur.fetchall()

    return render_template('holdings.html', user=session['user'], holdings=holdings)

@app.route('/news.html')
def news(company='all'):
    cur = conn.cursor()
    
    if company == 'all':
        query = '''
            SELECT date_of_news, title, related_company, C.sector, GROUP_CONCAT(sources) AS sources 
            FROM news N
            INNER JOIN company_profile C ON N.related_company = C.symbol
            GROUP BY date_of_news, title, related_company, C.sector;
        '''
        cur.execute(query)
    else:
        query = '''
            SELECT date_of_news, title, related_company, related_sector, sources 
            FROM news 
            WHERE related_company = %s
            GROUP BY date_of_news, title, related_company, related_sector, sources;
        '''
        cur.execute(query, [company])

    rv = cur.fetchall()
    return render_template('news.html', values=rv)


if __name__ == '__main__':
    app.run(debug=True)