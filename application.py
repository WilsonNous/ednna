from app import app
from ednna.api.eddy_query import create_eddy_query_blueprint
from ednna.api.orchestration import create_orchestration_blueprint
from ednna.governance.feature_flags import approval_api_enabled


app.register_blueprint(create_orchestration_blueprint())
app.register_blueprint(create_eddy_query_blueprint())

if approval_api_enabled():
    from ednna.api.approvals import create_approval_blueprint
    from ednna.governance.mysql_stores import MySQLApprovalStore
    from ednna.identity.bootstrap import build_oidc_authenticator
    from ednna.settings import DatabaseSettings

    app.register_blueprint(
        create_approval_blueprint(
            build_oidc_authenticator(),
            MySQLApprovalStore(DatabaseSettings.from_env()),
        )
    )
