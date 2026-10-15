from __future__ import annotations

import plistlib
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKFLOW_DIR = ROOT / "SimpleLogin"
OUTPUT = ROOT.parent / "dist" / "SimpleLogin.alfredworkflow"


def uid() -> str:
    return str(uuid.uuid4()).upper()


def script_filter(
    *,
    uid_value: str,
    keyword: str | None,
    title: str,
    subtext: str,
    script_file: str,
    argumenttype: int = 1,
    alfredfiltersresults: bool = True,
) -> dict:
    config = {
        "title": title,
        "subtext": subtext,
        "withspace": keyword is not None,
        "argumenttype": argumenttype,
        "argumenttrimmode": 0,
        "argumenttreatemptyqueryasnil": True,
        "alfredfiltersresults": alfredfiltersresults,
        "alfredfiltersresultsmatchmode": 0,
        "queuedelaycustom": 3,
        "queuedelayimmediatelyinitially": True,
        "queuedelaymode": 0,
        "queuemode": 2,
        "runningsubtext": "Loading SimpleLogin…",
        "script": f'./{script_file} "{{query}}"',
        "scriptfile": "",
        "scriptargtype": 0,
        "type": 11,
        "escaping": 4,
    }
    if keyword is not None:
        config["keyword"] = keyword
    return {
        "uid": uid_value,
        "type": "alfred.workflow.input.scriptfilter",
        "version": 3,
        "config": config,
    }


def argument_vars(
    *, uid_value: str, variables: dict[str, str], argument: str = ""
) -> dict:
    """Clear or replace the argument while carrying values as variables."""
    return {
        "uid": uid_value,
        "type": "alfred.workflow.utility.argument",
        "version": 1,
        "config": {
            "argument": argument,
            "passthroughargument": False,
            "variables": variables,
        },
    }


def text_input(*, uid_value: str, text: str, subtext: str) -> dict:
    return {
        "uid": uid_value,
        "type": "alfred.workflow.input.keyword",
        "version": 1,
        "config": {
            "text": text,
            "subtext": subtext,
            "withspace": False,
            "argumenttype": 0,
        },
    }


def run_script(*, uid_value: str, script_file: str, arguments: str = "") -> dict:
    return {
        "uid": uid_value,
        "type": "alfred.workflow.action.script",
        "version": 2,
        "config": {
            "script": f'./{script_file} {arguments}'.rstrip(),
            "scriptfile": "",
            "scriptargtype": 0,
            "type": 11,
            "escaping": 4,
            "concurrently": False,
        },
    }


def notification(*, uid_value: str, title: str) -> dict:
    return {
        "uid": uid_value,
        "type": "alfred.workflow.output.notification",
        "version": 1,
        "config": {
            "lastpathcomponent": False,
            "onlyshowifquerypopulated": True,
            "removeextension": False,
            "text": "{query}",
            "title": title,
        },
    }


def connect(
    source: str,
    destination: str,
    source_output: str | None = None,
    *,
    modifiers: int = 0,
    modifiersubtext: str = "",
) -> dict:
    edge = {
        "destinationuid": destination,
        "modifiers": modifiers,
        "modifiersubtext": modifiersubtext,
        "vitoclose": False,
    }
    if source_output is not None:
        edge["sourceoutputuid"] = source_output
    return edge


ids = {name: uid() for name in (
    "aliases_filter", "alias_vars", "recipient_input", "create_reverse",
    "contacts_aliases", "contacts_vars", "contacts_filter", "contacts_clipboard",
    "new_aliases_filter", "custom_vars", "prefix_input", "create_custom",
    "setup_filter", "setup_condition", "install", "login_reset", "login_input",
    "login_capture", "login_action", "login_cleanup", "logout",
    "result_condition", "success_notice", "error_notice", "error_large_type",
)}
setup_condition_ids = {name: uid() for name in ("install", "login", "logout")}
result_error_id = uid()

setup_condition = {
    "uid": ids["setup_condition"],
    "type": "alfred.workflow.utility.conditional",
    "version": 1,
    "config": {
        "conditions": [
            {
                "inputstring": "",
                "matchcasesensitive": False,
                "matchmode": 0,
                "matchstring": name,
                "outputlabel": name,
                "uid": setup_condition_ids[name],
            }
            for name in ("install", "login", "logout")
        ],
        "elselabel": "else",
        "hideelse": True,
    },
}

result_condition = {
    "uid": ids["result_condition"],
    "type": "alfred.workflow.utility.conditional",
    "version": 1,
    "config": {
        "conditions": [
            {
                "inputstring": "",
                "matchcasesensitive": False,
                "matchmode": 4,
                "matchstring": ".*ERROR:.*",
                "outputlabel": "error",
                "uid": result_error_id,
            }
        ],
        "elselabel": "success",
        "hideelse": False,
    },
}

workflow = {
    "bundleid": "com.simplelogin.cli.alfred",
    "name": "SimpleLogin",
    "createdby": "SimpleLogin CLI",
    "description": "Browse aliases, create custom/reverse aliases, inspect contacts, and manage setup.",
    "webaddress": "https://github.com/pSpitzner/alfred_simplelogin_cli",
    "variables": {
        "UV": "",
        "SIMPLELOGIN_CLI": "./.venv/bin/sl",
    },
    "userconfigurationconfig": [
        {
            "config": {
                "default": "",
                "placeholder": "/opt/homebrew/bin/uv",
                "required": False,
                "trim": True,
            },
            "description": "Full path to the uv executable used by Install / Update.",
            "label": "uv executable (UV)",
            "type": "textfield",
            "variable": "UV",
        },
        {
            "config": {
                "default": "./.venv/bin/sl",
                "placeholder": "./.venv/bin/sl",
                "required": True,
                "trim": True,
            },
            "description": "CLI installed by uv sync inside this workflow folder.",
            "label": "SimpleLogin CLI (SIMPLELOGIN_CLI)",
            "type": "textfield",
            "variable": "SIMPLELOGIN_CLI",
        },
    ],
    "version": "1.0",
    "disabled": False,
    "readme": (
        "Use `sl` to browse aliases. The selected alias ID is saved as a workflow "
        "variable, then Alfred starts a blank recipient input. Use `slc` to browse "
        "aliases and contacts. Use `slnew` to choose a suffix and enter a custom "
        "alias prefix. `slsetup` offers Install / Update, Log In, and Log Out. "
        "Log In uses Alfred text input; the token is visible while entered and "
        "may be saved in Alfred history. Errors produce a notification and an "
        "Alfred Large Type message. Set `UV` to the uv executable; "
        "`SIMPLELOGIN_CLI` defaults to `./.venv/bin/sl`."
    ),
    "objects": [
        script_filter(
            uid_value=ids["aliases_filter"], keyword="sl",
            title="SimpleLogin Aliases",
            subtext="Return to create a reverse alias · ⌥Return to view existing ones",
            script_file="aliases.sh",
            alfredfiltersresults=False,
        ),
        argument_vars(
            uid_value=ids["alias_vars"],
            variables={
                "alias_id": "{var:alias_id}",
                "alias_email": "{var:alias_email}",
            },
        ),
        text_input(
            uid_value=ids["recipient_input"],
            text="Recipient for {var:alias_email}",
            subtext="Type the recipient email, then press Return",
        ),
        run_script(
            uid_value=ids["create_reverse"], script_file="create-reverse.sh",
            arguments='"$alias_id" "{query}"',
        ),
        script_filter(
            uid_value=ids["contacts_aliases"], keyword="slc",
            title="SimpleLogin Contacts",
            subtext="Choose an alias to see its reverse aliases",
            script_file="aliases.sh",
            alfredfiltersresults=False,
        ),
        argument_vars(
            uid_value=ids["contacts_vars"],
            variables={
                "alias_id": "{var:alias_id}",
                "alias_email": "{var:alias_email}",
            },
        ),
        script_filter(
            uid_value=ids["contacts_filter"], keyword=None,
            title="Reverse Aliases for {var:alias_email}",
            subtext="Select an address to copy it",
            script_file="contacts.sh",
        ),
        {
            "uid": ids["contacts_clipboard"],
            "type": "alfred.workflow.output.clipboard",
            "version": 2,
            "config": {"autopaste": False, "clipboardtext": "", "transient": False},
        },
        script_filter(
            uid_value=ids["new_aliases_filter"], keyword="slnew",
            title="Create a Custom SimpleLogin Alias",
            subtext="Choose an available suffix",
            script_file="new-aliases.sh",
        ),
        argument_vars(
            uid_value=ids["custom_vars"],
            variables={
                "signed_suffix": "{var:signed_suffix}",
                "mailbox_id": "{var:mailbox_id}",
                "prefix_suggestion": "{var:prefix_suggestion}",
                "alias_suffix": "{var:alias_suffix}",
            },
        ),
        text_input(
            uid_value=ids["prefix_input"],
            text="Alias prefix for {var:alias_suffix}",
            subtext="Suggested prefix: {var:prefix_suggestion}",
        ),
        run_script(
            uid_value=ids["create_custom"], script_file="create-custom.sh",
            arguments='"{query}" "$signed_suffix" "$mailbox_id"',
        ),
        script_filter(
            uid_value=ids["setup_filter"], keyword="slsetup",
            title="SimpleLogin Setup",
            subtext="Choose Install / Update, Log In, or Log Out",
            script_file="setup-menu.sh",
        ),
        setup_condition,
        run_script(uid_value=ids["install"], script_file="setup.sh"),
        argument_vars(uid_value=ids["login_reset"], variables={}),
        text_input(
            uid_value=ids["login_input"],
            text="SimpleLogin API token",
            subtext="Visible while entered; press Return to verify and save",
        ),
        argument_vars(
            uid_value=ids["login_capture"],
            variables={"login_token": "{query}"},
        ),
        run_script(uid_value=ids["login_action"], script_file="login.sh"),
        argument_vars(
            uid_value=ids["login_cleanup"],
            variables={"login_token": ""},
            argument="{query}",
        ),
        run_script(uid_value=ids["logout"], script_file="logout.sh"),
        result_condition,
        notification(uid_value=ids["success_notice"], title="SimpleLogin"),
        notification(uid_value=ids["error_notice"], title="SimpleLogin Error"),
        {
            "uid": ids["error_large_type"],
            "type": "alfred.workflow.output.largetype",
            "version": 3,
            "config": {
                "alignment": 0,
                "backgroundcolor": "",
                "fadespeed": 0,
                "fillmode": 0,
                "font": "",
                "ignoredynamicplaceholders": False,
                "largetypetext": "{query}",
                "textcolor": "",
                "wrapat": 50,
            },
        },
    ],
    "connections": {
        ids["aliases_filter"]: [
            connect(ids["aliases_filter"], ids["alias_vars"]),
            connect(
                ids["aliases_filter"],
                ids["contacts_vars"],
                modifiers=524288,
                modifiersubtext="View existing reverse aliases",
            ),
        ],
        ids["alias_vars"]: [connect(ids["alias_vars"], ids["recipient_input"])],
        ids["recipient_input"]: [connect(ids["recipient_input"], ids["create_reverse"])],
        ids["create_reverse"]: [connect(ids["create_reverse"], ids["result_condition"])],
        ids["contacts_aliases"]: [connect(ids["contacts_aliases"], ids["contacts_vars"])],
        ids["contacts_vars"]: [connect(ids["contacts_vars"], ids["contacts_filter"])],
        ids["contacts_filter"]: [connect(ids["contacts_filter"], ids["contacts_clipboard"])],
        ids["contacts_clipboard"]: [],
        ids["new_aliases_filter"]: [connect(ids["new_aliases_filter"], ids["custom_vars"])],
        ids["custom_vars"]: [connect(ids["custom_vars"], ids["prefix_input"])],
        ids["prefix_input"]: [connect(ids["prefix_input"], ids["create_custom"])],
        ids["create_custom"]: [connect(ids["create_custom"], ids["result_condition"])],
        ids["setup_filter"]: [connect(ids["setup_filter"], ids["setup_condition"])],
        ids["setup_condition"]: [
            connect(ids["setup_condition"], ids["install"], setup_condition_ids["install"]),
            connect(ids["setup_condition"], ids["login_reset"], setup_condition_ids["login"]),
            connect(ids["setup_condition"], ids["logout"], setup_condition_ids["logout"]),
        ],
        ids["install"]: [connect(ids["install"], ids["result_condition"])],
        ids["login_reset"]: [connect(ids["login_reset"], ids["login_input"])],
        ids["login_input"]: [connect(ids["login_input"], ids["login_capture"])],
        ids["login_capture"]: [connect(ids["login_capture"], ids["login_action"])],
        ids["login_action"]: [connect(ids["login_action"], ids["login_cleanup"])],
        ids["login_cleanup"]: [connect(ids["login_cleanup"], ids["result_condition"])],
        ids["logout"]: [connect(ids["logout"], ids["result_condition"])],
        ids["result_condition"]: [
            connect(ids["result_condition"], ids["success_notice"]),
            connect(ids["result_condition"], ids["error_notice"], result_error_id),
            connect(ids["result_condition"], ids["error_large_type"], result_error_id),
        ],
        ids["success_notice"]: [],
        ids["error_notice"]: [],
        ids["error_large_type"]: [],
    },
    "uidata": {
        ids[name]: {"xpos": 100 + (index % 4) * 220, "ypos": 100 + (index // 4) * 150}
        for index, name in enumerate(ids)
    },
}

WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
(WORKFLOW_DIR / "info.plist").write_bytes(
    plistlib.dumps(workflow, fmt=plistlib.FMT_XML, sort_keys=False)
)

workflow_files = {
    "info.plist", "icon.png", "aliases.sh", "contacts.sh", "create-reverse.sh",
    "create-custom.sh", "new-aliases.sh", "setup.sh", "setup-menu.sh",
    "login.sh", "logout.sh", "README.md",
}
with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(workflow_files):
        archive.write(WORKFLOW_DIR / name, arcname=name)
    for name in ("logo.svg", "pyproject.toml", "uv.lock"):
        archive.write(ROOT.parent / name, arcname=name)
    for source in sorted((ROOT.parent / "src" / "simplelogin_cli").glob("*.py")):
        archive.write(source, arcname=f"src/simplelogin_cli/{source.name}")

print(OUTPUT)
