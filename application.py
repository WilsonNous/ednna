from app import app
from ednna.api.eddy_query import create_eddy_query_blueprint
from ednna.api.orchestration import create_orchestration_blueprint


app.register_blueprint(create_orchestration_blueprint())
app.register_blueprint(create_eddy_query_blueprint())
