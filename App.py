from flask import Flask
from config import Config
from extensions import login_manager

def create_app():
    app = Flask(__name__,
                template_folder='frontend/templates',
                static_folder='frontend/static')
    app.config.from_object(Config)

    login_manager.init_app(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.customer import customer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(customer_bp)

    # Context processor to make cart count available in all templates
    @app.context_processor
    def inject_cart_count():
        from flask_login import current_user
        from database import execute_query

        cart_count = 0
        if current_user.is_authenticated and hasattr(current_user, 'is_customer') and current_user.is_customer:
            query = """
                SELECT COALESCE(SUM(ci.Quantity), 0) as total
                FROM CART_ITEM ci
                JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                WHERE sc.Customer_Username = %s
            """
            result = execute_query(query, (current_user.username,), fetch_one=True)
            cart_count = int(result['total']) if result else 0

        return dict(cart_count=cart_count)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
