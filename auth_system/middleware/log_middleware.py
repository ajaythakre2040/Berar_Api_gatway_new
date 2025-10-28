import uuid
import json
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from auth_system.models import TblUser
from auth_system.models.login_session import LoginSession


class APILogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # --- Step 1: Authorization Token ---
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        request._token = token

        # --- Step 2: Try to load request body ---
        try:
            if request.body:
                request._body_data = json.loads(request.body.decode("utf-8"))
            else:
                request._body_data = {}
        except Exception:
            request._body_data = {}

        # --- Step 3: Get user-provided unique_id from body ---
        user_provided_unique_id = request._body_data.get("unique_id")

        # --- Step 4: Get session_uuid from token, if available ---
        session_uuid = None
        if token:
            try:
                session = LoginSession.objects.filter(
                    token=token, is_active=True
                ).first()
                if session:
                    session_uuid = str(session.pk)  # ✅ FIXED LINE
            except Exception as e:
                print(f"[Middleware] Error fetching session: {e}")

        # --- ✅ Step 5: Final priority: user_provided > session_uuid > random UUID ---
        request.uniqid = user_provided_unique_id or session_uuid or str(uuid.uuid4())

        # --- Step 6: Store in session (if enabled) ---
        request.session["session_uuid"] = request.uniqid
        request.session.modified = True

        # --- Step 7: Parse query parameters ---
        request._query_params = _flatten_querydict(
            request.GET,
            exclude_keys=["page", "page_size", "limit", "offset"],
        )

    def process_response(self, request, response):
        try:
            if getattr(request, "_log_saved", False):
                return response

            try:
                resolve(request.path_info)
            except Resolver404:
                return response

            path = request.path_info
            method = request.method

            EXCLUDED_PATHS = ["/admin/", "/static/", "/health/", "/test/"]
            if any(path.startswith(p) for p in EXCLUDED_PATHS):
                return response

            if path in ["/auth_system/login/", "/auth_system/logout/"]:
                app_name = "auth_system"
            elif path.startswith("/auth_system/"):
                app_name = "auth_system"
            else:
                app_name = "auth_system"

            user = getattr(request, "user", None)
            user_obj = user if user and user.is_authenticated else None
            token = request._token
            body_data = getattr(request, "_body_data", {})
            query_params = getattr(request, "_query_params", {})

            if not user_obj:
                if path == "/auth_system/login/":
                    username = body_data.get("username")
                    if username:
                        try:
                            if username.isdigit() and len(username) == 10:
                                user_obj = TblUser.objects.filter(
                                    mobile_number=username
                                ).first()
                            elif "@" in username:
                                user_obj = TblUser.objects.filter(
                                    email=username
                                ).first()
                            else:
                                user_obj = TblUser.objects.filter(
                                    username=username
                                ).first()
                        except Exception:
                            user_obj = None
                elif path == "/auth_system/logout/" and token:
                    try:
                        session = LoginSession.objects.filter(
                            token=token, is_active=True
                        ).first()
                        if session and hasattr(session, "user"):
                            user_obj = session.user
                    except Exception as e:
                        print(f"[Middleware] Error fetching logout session user: {e}")

            if path == "/auth_system/login/":
                if (
                    response.status_code == 200
                    and hasattr(response, "content")
                    and response.get("Content-Type", "").startswith("application/json")
                ):
                    try:
                        data = json.loads(response.content.decode("utf-8"))
                        new_uuid = data.get("session_uuid")
                        if new_uuid:
                            request.uniqid = new_uuid
                            request.session["session_uuid"] = new_uuid
                            request.session.modified = True
                    except Exception as e:
                        print(f"[Middleware] Failed to parse login response UUID: {e}")

            if method == "GET" and not query_params:
                request_data = {"message": "Full data fetched"}
            else:
                request_data = {**body_data, **query_params}

            APILog = self._import_apilog_model(app_name)
            if not APILog:
                return response

            log_entry = APILog(
                uniqid=request.uniqid,
                user=user_obj,
                method=method,
                endpoint=path,
                request_data=request_data,
                response_status=response.status_code,
            )

            try:
                if hasattr(response, "content") and response.get(
                    "Content-Type", ""
                ).startswith("application/json"):
                    log_entry.response_data = json.loads(
                        response.content.decode("utf-8")
                    )
                else:
                    log_entry.response_data = None
            except Exception:
                log_entry.response_data = None

            log_entry.save()
            request._log_saved = True

        except Exception as e:
            print(f"[Middleware] APILog error: {e}")

        return response

    def _import_apilog_model(self, app_name):
        try:
            module = __import__(f"{app_name}.models", fromlist=["APILog"])
            return getattr(module, "APILog")
        except (ImportError, AttributeError) as e:
            print(f"[Middleware] Could not import APILog from {app_name}.models: {e}")
            return None


def _flatten_querydict(querydict, exclude_keys=None):
    exclude_keys = exclude_keys or []
    return {
        key: (value[0] if len(value) == 1 else value)
        for key, value in querydict.lists()
        if key not in exclude_keys
    }
