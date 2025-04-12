from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_bcrypt import Bcrypt
import psycopg2
from functools import wraps
from flask import Flask, make_response
import json
from datetime import datetime, timedelta
import os
from collections import defaultdict


app = Flask(__name__,
            template_folder='templates',
            static_folder='templates',
            static_url_path='')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key_here'

bcrypt = Bcrypt(app)

def create_app():
   return app

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="123",
        client_encoding='utf-8'
    )
    return conn

# Конфигурация
LOG_DIR = 'analytics_logs'
os.makedirs(LOG_DIR, exist_ok=True)

def get_visitor_id():
    """Получение или создание ID посетителя"""
    visitor_id = request.cookies.get('visitor_id')
    if not visitor_id:
        visitor_id = f"vis_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    return visitor_id

def log_visit(page):
    """Логирование посещения страницы"""
    visitor_id = get_visitor_id()
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'visitor_id': visitor_id,
        'page': page,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string
    }
    
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIR, f'visits_{today}.log')
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_data) + '\n')
    
    return visitor_id

@app.route('/api/analytics/data')
def analytics_data():
    days = request.args.get('days', default=7, type=int)
    
    # Get your analytics data (implement this function)
    analytics_data = get_analytics_data(days)  
    
    # Format the response as expected by frontend
    response = {
        "labels": list(analytics_data['page_stats'].keys()),
        "sales": list(analytics_data['sales_data'].values()),
        "pageStats": []
    }
    
    for page, views in analytics_data['page_stats'].items():
        unique_visitors = analytics_data['unique_visitors'].get(page, 0)
        sales = analytics_data['sales_data'].get(page, 0)
        conversion_rate = (sales / views * 100) if views > 0 else 0
        
        response['pageStats'].append({
            "path": page,
            "views": views,
            "unique_visitors": unique_visitors,
            "conversion_rate": round(conversion_rate, 1)
        })
    
    return jsonify(response)

def get_analytics_data(days=7):
    """Анализ данных за последние N дней"""
    page_stats = defaultdict(int)
    visitor_stats = defaultdict(set)
    sales_data = defaultdict(float)
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Анализ посещений
        visit_file = os.path.join(LOG_DIR, f'visits_{date}.log')
        if os.path.exists(visit_file):
            with open(visit_file) as f:
                for line in f:
                    data = json.loads(line)
                    page_stats[data['page']] += 1
                    visitor_stats[data['page']].add(data['visitor_id'])
        
        # Анализ продаж
        sales_file = os.path.join(LOG_DIR, f'sales_{date}.log')
        if os.path.exists(sales_file):
            with open(sales_file) as f:
                for line in f:
                    data = json.loads(line)
                    sales_data[data['page']] += data['amount']
    
    return {
        'page_stats': dict(page_stats),
        'unique_visitors': {k: len(v) for k, v in visitor_stats.items()},
        'sales_data': dict(sales_data)
    }

@app.route('/track-page')
def track_page():
    """Трекинг посещения страницы"""
    page = request.args.get('page', '/')
    visitor_id = log_visit(page)
    
    response = make_response('OK')
    response.set_cookie('visitor_id', visitor_id, max_age=30*24*60*60)
    return response

@app.route('/track-sale', methods=['POST'])
def track_sale():
    """Трекинг продажи"""
    data = request.json
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'page': data.get('page', '/'),
        'product_id': data['product_id'],
        'amount': data['amount'],
        'visitor_id': get_visitor_id()
    }
    
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIR, f'sales_{today}.log')
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_data) + '\n')
    
    return jsonify({'status': 'success'})

@app.route('/analytic')
def analytics_dashboard():
    """Страница аналитики"""
    analytics_data = get_analytics_data()
    return render_template('analytic.html', **analytics_data)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products LIMIT 4;')
    featured_products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', products=featured_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] 
        full_name = request.form['full_name']
        
        if len(password) < 5:
            flash('Пароль должен содержать минимум 5 символов', 'danger')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                'INSERT INTO users (email, password, full_name) VALUES (%s, %s, %s)',
                (email, password, full_name)  
            )
            conn.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            flash('Email уже используется', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, email, password FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        
        if user:
            stored_password = user[2]  
            if stored_password == password:  
                session['user_id'] = user[0]
                session['email'] = user[1]
                flash('Вы успешно вошли в систему', 'success')
                cur.close()
                conn.close()
                return redirect(url_for('account'))
        
        flash('Неверный email или пароль', 'danger')
        cur.close()
        conn.close()
    
    return render_template('login.html')


@app.route('/account')
@login_required
def account():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Получаем данные пользователя
        cur.execute('SELECT id, full_name, email, phone, address, created_at FROM users WHERE id = %s', 
                   (session['user_id'],))
        user = dict(zip([col[0] for col in cur.description], cur.fetchone())) if cur.rowcount else None

        # Получаем заказы с товарами
        orders = []
        cur.execute('''
            SELECT id, total, status, payment_method, created_at 
            FROM orders 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        
        for order_row in cur.fetchall():
            order = dict(zip(['id', 'total', 'status', 'payment_method', 'created_at'], order_row))
            
            # Получаем товары для заказа
            cur.execute('''
                SELECT p.name, oi.quantity, oi.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            ''', (order['id'],))
            
            order['items'] = [dict(zip(['name', 'quantity', 'price'], item)) for item in cur.fetchall()]
            orders.append(order)

        return render_template('account.html', user=user, orders=orders)

    except Exception as e:
        flash(f'Ошибка загрузки данных: {str(e)}', 'danger')
        return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()

@app.route('/product, <int:product_id>')
def product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    columns = [desc[0] for desc in cur.description]  # Получаем названия колонок
    product_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if not product_data:
        flash('Товар не найден', 'danger')
        return redirect(url_for('catalog'))
    
    # Преобразуем кортеж в словарь
    product = dict(zip(columns, product_data))
    return render_template('product.html', product=product)

@app.route('/catalog')
def catalog():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products;')
    columns = [desc[0] for desc in cur.description]
    products = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template('catalog.html', products=products)

@app.route('/api/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID is required'}), 400
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be positive'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid quantity'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существует ли товар
        cur.execute('SELECT id FROM products WHERE id = %s', (product_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Проверяем есть ли уже товар в корзине
        cur.execute('SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s', 
                   (session['user_id'], product_id))
        existing_item = cur.fetchone()
        
        if existing_item:
            new_quantity = existing_item[0] + quantity
            cur.execute('UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s',
                        (new_quantity, session['user_id'], product_id))
        else:
            cur.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)',
                        (session['user_id'], product_id, quantity))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'cart_count': get_cart_count(session['user_id'])
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

def get_cart_count(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE user_id = %s', (user_id,))
        count = cur.fetchone()[0]
        return count
    finally:
        cur.close()
        conn.close()

@app.route('/api/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Удаляем товар из корзины пользователя
        cur.execute('''
            DELETE FROM cart 
            WHERE user_id = %s AND product_id = %s
            RETURNING quantity
        ''', (session['user_id'], product_id))
        
        deleted_row = cur.fetchone()
        
        if not deleted_row:
            return jsonify({'success': False, 'error': 'Product not found in cart'}), 404
        
        # Получаем текущее количество оставшихся товаров в корзине
        cur.execute('SELECT COUNT(*) FROM cart WHERE user_id = %s', (session['user_id'],))
        remaining_items = cur.fetchone()[0]
        
        conn.commit()
        
        # Получаем обновленное количество товаров в корзине
        cart_count = get_cart_count(session['user_id'])
        
        return jsonify({
            'success': True, 
            'cart_count': cart_count,
            'is_empty': remaining_items == 0,
            'message': 'Product removed from cart'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/cancel_order, <int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем, что заказ принадлежит пользователю и еще не выполнен
        cur.execute('''
            UPDATE orders 
            SET status = 'cancelled' 
            WHERE id = %s AND user_id = %s AND status = 'processing'
            RETURNING id
        ''', (order_id, session['user_id']))
        
        if cur.rowcount == 0:
            return jsonify({'success': False, 'error': 'Order cannot be cancelled'}), 400
        
        conn.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/cart')
@login_required
def cart():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT p.id, p.name, p.price, p.image, c.quantity 
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    ''', (session['user_id'],))
    
    columns = [desc[0] for desc in cur.description]
 
    cart_items = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    cur.close()
    conn.close()
    
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Получаем данные пользователя
        cur.execute('''
            SELECT full_name, email, phone, address
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        user_data = cur.fetchone()
        
        # Получаем товары в корзине
        cur.execute('''
            SELECT 
                p.id,
                p.name,
                p.price,
                c.quantity,
                p.price * c.quantity as total_price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        ''', (session['user_id'],))
        
        columns = [desc[0] for desc in cur.description]
        cart_items = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        # Вычисляем общую сумму
        total = sum(item['total_price'] for item in cart_items)
        
        if request.method == 'POST':
            # Получаем данные из формы
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            comment = request.form.get('comment')
            payment_method = request.form.get('payment')
            
            # Создаем заказ
            cur.execute('''
                INSERT INTO orders (user_id, total, status, payment_method, delivery_address, comment)
                VALUES (%s, %s, 'processing', %s, %s, %s)
                RETURNING id
            ''', (session['user_id'], total, payment_method, address, comment))
            order_id = cur.fetchone()[0]
            
            # Переносим товары из корзины в заказ
            for item in cart_items:
                cur.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, item['id'], item['quantity'], item['price']))
            
            # Очищаем корзину
            cur.execute('DELETE FROM cart WHERE user_id = %s', (session['user_id'],))
            
            # Обновляем данные пользователя
            cur.execute('''
                UPDATE users 
                SET full_name = %s, email = %s, phone = %s, address = %s 
                WHERE id = %s
            ''', (name, email, phone, address, session['user_id']))
            
            conn.commit()
            
            flash(f'Заказ успешно оформлен! Номер вашего заказа: #{order_id}', 'success')
            return redirect(url_for('account'))
            
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при оформлении заказа: {str(e)}', 'danger')
        return redirect(url_for('checkout'))
    finally:
        cur.close()
        conn.close()
    
    return render_template(
        'checkout.html',
        user=user_data,
        cart_items=cart_items,
        total=total
    )



@app.route('/orders_history')
@login_required
def orders_history():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Единый запрос для заказов и товаров
        cur.execute('''
            SELECT 
                o.id, 
                o.created_at, 
                o.status, 
                o.total,
                o.delivery_address,
                o.payment_method,
                o.comment,
                p.name AS name,
                oi.quantity AS quantity,
                oi.price AS price
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC, o.id, p.name
        ''', (session['user_id'],))
        
        orders = []
        for order_row in cur.fetchall():
            order = {
                'id': order_row[0],
                'date': order_row[1],
                'status': order_row[2],
                'total': float(order_row[3]),
                'delivery_address': order_row[4],
                'payment_method': order_row[5],
                'comment': order_row[6],
                'name': order_row[7],    
                'quantity': order_row[8], 
                'price': order_row[9]         
            }         
            
            orders.append(order)
        
        # Получаем статистику
        cur.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(total) as total_spent,
                MIN(created_at) as first_order_date
            FROM orders
            WHERE user_id = %s
        """, (session['user_id'],))
        
        stats = cur.fetchone()
        order_stats = {
            'total_orders': stats[0],
            'total_spent': float(stats[1]) if stats[1] else 0,
            'first_order_date': stats[2]
        }
        
        
        return render_template(
            'orders_history.html',
            orders=orders,
            order_stats=order_stats
        )
    
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        flash("Ошибка загрузки истории заказов", "error")
        return redirect(url_for('account'))
    finally:
        cur.close()
        conn.close()


@app.route('/logout-on-close')
def logout_on_close():
    session.clear()
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()  # Очищаем сессию
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)