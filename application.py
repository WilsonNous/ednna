from app import app
from ednna.api.eddy_query import create_eddy_query_blueprint
from ednna.api.orchestration import create_orchestration_blueprint
from ednna.api.readiness import create_readiness_blueprint
from ednna.api.runtime import create_runtime_blueprint
from ednna.governance.action_feature_flags import action_api_enabled
from ednna.governance.feature_flags import approval_api_enabled
from ednna.events.feature_flags import event_ingress_api_enabled
from ednna.orchestration.multiagent_feature_flags import multiagent_query_api_enabled


app.register_blueprint(create_orchestration_blueprint())
app.register_blueprint(create_readiness_blueprint())
app.register_blueprint(create_runtime_blueprint())
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


if action_api_enabled():
    from ednna.api.actions import create_action_blueprint
    from ednna.bootstrap import build_eddy_gateway
    from ednna.governance.mysql_action_ledger import MySQLActionExecutionLedger
    from ednna.governance.mysql_stores import MySQLApprovalStore, MySQLIdempotencyStore
    from ednna.identity.bootstrap import build_oidc_authenticator
    from ednna.settings import DatabaseSettings

    action_db = DatabaseSettings.from_env()
    app.register_blueprint(
        create_action_blueprint(
            build_oidc_authenticator(),
            build_eddy_gateway(),
            MySQLApprovalStore(action_db),
            MySQLIdempotencyStore(action_db),
            MySQLActionExecutionLedger(action_db),
        )
    )


if multiagent_query_api_enabled():
    from ednna.api.multiagent import create_multiagent_query_blueprint
    from ednna.bootstrap import build_multiagent_runtime
    from ednna.identity.bootstrap import build_oidc_authenticator

    multiagent_registry, multiagent_gateway, multiagent_availability = (
        build_multiagent_runtime()
    )
    app.register_blueprint(
        create_multiagent_query_blueprint(
            build_oidc_authenticator(),
            multiagent_registry,
            multiagent_gateway,
            multiagent_availability,
        )
    )


if event_ingress_api_enabled():
    from ednna.api.events import create_event_ingress_blueprint
    from ednna.events.bootstrap import build_event_router
    from ednna.events.mysql_store import MySQLEventStore
    from ednna.events.service import EventService
    from ednna.governance.mysql_stores import MySQLApprovalStore
    from ednna.identity.bootstrap import build_oidc_authenticator
    from ednna.settings import DatabaseSettings

    event_db = DatabaseSettings.from_env()
    event_store = MySQLEventStore(event_db)
    approval_store = MySQLApprovalStore(event_db)
    app.register_blueprint(
        create_event_ingress_blueprint(
            build_oidc_authenticator(),
            EventService(event_store, build_event_router(approval_store)),
        )
    )
