from datetime import datetime, timedelta
from EcommerceStore import create_app
from flask import g
from EcommerceStore.models import Category

app = create_app(h)

if __name__ == "__main__":
    app.jinja_env.globals['float'] = float
    app.jinja_env.globals['len'] = len
    app.jinja_env.globals['str'] = str
    app.jinja_env.globals['int'] = int
    app.jinja_env.globals['round'] = round
    app.jinja_env.globals['timedelta'] = timedelta
    app.jinja_env.globals['datetime'] = datetime

    @app.before_request
    def load_categories():
        '''
        This method is called before any request is made.
        It ensures that several builtin types are available in html layouts. 
        '''
        categories = Category.query.all()
        parent_categories = []
        for parent in categories:
            if parent.id == parent.parent_id:
                parent_categories.append(parent)

        # g in flask is a global variable that is accessible from anywhere.
        g.categories = parent_categories
        g.length = len(parent_categories)
    app.run(debug=True)

