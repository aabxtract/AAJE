import html
import json
import re
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import BASE_DIR
from app.redis import clear_flow_session, get_flow_session

router = APIRouter()

FLOW_FILES = {
    "onboarding_profile": "01_profile_setup.json",
    "business_setup": "02_business_setup.json",
    "pin_setup": "03_pin_setup.json",
    "pin_confirm": "04_pin_confirm.json",
    "business_passport": "05_business_passport.json",
}

TOKEN_PATTERN = re.compile(r"^\$\{(form|data)\.([A-Za-z0-9_]+)\}$")
INLINE_DATA_PATTERN = re.compile(r"\$\{data\.([A-Za-z0-9_]+)\}")


def _flow_path(flow_type: str) -> Path:
    try:
        filename = FLOW_FILES[flow_type]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown Flow") from exc
    return BASE_DIR.parent / "whatsapp_flows" / filename


def _load_flow(flow_type: str) -> dict:
    return json.loads(_flow_path(flow_type).read_text(encoding="utf-8"))


def _render_text(template: str, data: dict) -> str:
    def replace(match: re.Match) -> str:
        return html.escape(str(data.get(match.group(1), "")))

    return INLINE_DATA_PATTERN.sub(replace, html.escape(template))


def _field_value(source: str, key: str, form_data: dict, screen_data: dict):
    if source == "form":
        return form_data.get(key, "")
    return screen_data.get(key, "")


def _resolve_payload(payload: dict, form_data: dict, screen_data: dict) -> dict:
    resolved = {}
    for key, value in payload.items():
        if isinstance(value, str):
            match = TOKEN_PATTERN.match(value)
            if match:
                resolved[key] = _field_value(match.group(1), match.group(2), form_data, screen_data)
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved


def _input_type(component: dict) -> str:
    kind = component.get("input-type") or "text"
    if kind == "password":
        return "password"
    if kind == "number":
        return "number"
    return "text"


def _render_component(component: dict, screen_data: dict) -> str:
    component_type = component.get("type")
    if component_type == "TextHeading":
        return f'<h1>{_render_text(component.get("text", ""), screen_data)}</h1>'
    if component_type == "TextSubheading":
        return f'<h2>{_render_text(component.get("text", ""), screen_data)}</h2>'
    if component_type == "TextBody":
        return f'<p>{_render_text(component.get("text", ""), screen_data)}</p>'
    if component_type == "TextInput":
        name = html.escape(component.get("name", ""))
        label = html.escape(component.get("label", name))
        required = " required" if component.get("required") else ""
        input_type = _input_type(component)
        return (
            f'<label><span>{label}</span>'
            f'<input name="{name}" type="{input_type}" autocomplete="off"{required}></label>'
        )
    if component_type == "Dropdown":
        name = html.escape(component.get("name", ""))
        label = html.escape(component.get("label", name))
        required = " required" if component.get("required") else ""
        source = component.get("data-source", "")
        options = []
        source_match = INLINE_DATA_PATTERN.fullmatch(source)
        if source_match:
            options = screen_data.get(source_match.group(1), [])
        option_html = ['<option value="">Select</option>']
        for option in options:
            value = html.escape(str(option.get("id", "")))
            title = html.escape(str(option.get("title", value)))
            option_html.append(f'<option value="{value}">{title}</option>')
        return f'<label><span>{label}</span><select name="{name}"{required}>{"".join(option_html)}</select></label>'
    if component_type == "Footer":
        action = component.get("on-click-action") or {}
        payload = html.escape(json.dumps(action.get("payload") or {}), quote=True)
        label = html.escape(component.get("label", "Continue"))
        return f'<input type="hidden" name="payload_json" value="{payload}"><button type="submit">{label}</button>'
    return ""


def _render_flow_page(flow: dict, flow_session: dict) -> str:
    screen = flow["screens"][0]
    screen_data = flow_session.get("data") or {}
    children = screen.get("layout", {}).get("children", [])
    form_children = []
    for child in children:
        form_children.extend(child.get("children", []) if child.get("type") == "Form" else [child])

    body = "\n".join(_render_component(component, screen_data) for component in form_children)
    title = html.escape(screen.get("title", "AAJE"))
    token = html.escape(flow_session["token"])
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
      :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; min-height: 100vh; background: #eef3ef; color: #14211b; display: grid; place-items: center; padding: 18px; }}
      main {{ width: min(100%, 430px); min-height: min(760px, calc(100vh - 36px)); background: #fff; border: 1px solid #dfe7e1; border-radius: 8px; box-shadow: 0 18px 50px rgba(11, 38, 25, .12); overflow: hidden; }}
      header {{ height: 58px; display: flex; align-items: center; padding: 0 18px; border-bottom: 1px solid #edf1ee; font-weight: 800; }}
      form {{ padding: 22px 18px 18px; display: grid; gap: 15px; }}
      h1 {{ margin: 0 0 2px; font-size: 22px; line-height: 1.2; letter-spacing: 0; }}
      h2 {{ margin: 10px 0 0; font-size: 15px; line-height: 1.25; letter-spacing: 0; }}
      p {{ margin: 0; color: #526158; line-height: 1.45; font-size: 14px; }}
      label {{ display: grid; gap: 7px; }}
      label span {{ color: #26352c; font-size: 13px; font-weight: 750; }}
      input, select {{ width: 100%; min-height: 46px; border: 1px solid #cfd9d2; border-radius: 7px; padding: 0 12px; font: inherit; background: #fff; color: #14211b; }}
      input:focus, select:focus {{ outline: 2px solid #128c7e33; border-color: #128c7e; }}
      button {{ width: 100%; min-height: 48px; border: 0; border-radius: 7px; background: #128c7e; color: #fff; font: inherit; font-weight: 800; cursor: pointer; margin-top: 6px; }}
      .secure {{ padding: 12px 18px; border-top: 1px solid #edf1ee; color: #64746b; font-size: 12px; line-height: 1.4; background: #fbfcfb; }}
    </style>
  </head>
  <body>
    <main>
      <header>AAJE Secure Flow</header>
      <form method="post" action="/flow/submit">
        <input type="hidden" name="token" value="{token}">
        {body}
      </form>
      <div class="secure">This secure browser flow mirrors the WhatsApp Flow experience while Meta Flow access is limited in test mode.</div>
    </main>
  </body>
</html>"""


def _done_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AAJE Flow Complete</title>
    <style>
      body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 18px; font-family: Inter, system-ui, sans-serif; background: #eef3ef; color: #14211b; }
      main { width: min(100%, 420px); text-align: center; background: #fff; border: 1px solid #dfe7e1; border-radius: 8px; padding: 28px 22px; }
      h1 { margin: 0 0 8px; font-size: 24px; letter-spacing: 0; }
      p { margin: 0; color: #526158; line-height: 1.45; }
    </style>
  </head>
  <body><main><h1>Submitted</h1><p>You can return to WhatsApp. AAJE is processing your secure response.</p></main></body>
</html>"""


@router.get("/flow", response_class=HTMLResponse)
async def browser_flow(token: str):
    flow_session = await get_flow_session(token)
    if not flow_session:
        raise HTTPException(status_code=404, detail="Flow link expired")
    flow_session["token"] = token
    flow = _load_flow(flow_session["type"])
    return _render_flow_page(flow, flow_session)


@router.post("/flow/submit", response_class=HTMLResponse)
async def submit_browser_flow(request: Request, token: str = Form(...), payload_json: str = Form("{}")):
    flow_session = await get_flow_session(token)
    if not flow_session:
        raise HTTPException(status_code=404, detail="Flow link expired")

    submitted = dict(await request.form())
    submitted.pop("token", None)
    submitted.pop("payload_json", None)
    payload_template = json.loads(payload_json)
    data = _resolve_payload(payload_template, submitted, flow_session.get("data") or {})

    from app.services.session import route_flow_response

    await route_flow_response(
        flow_session["whatsapp_no"],
        {
            "name": flow_session["type"],
            "body": "Browser Flow response",
            "flow_token": token,
            "data": data,
        },
    )
    await clear_flow_session(token)
    return _done_page()
