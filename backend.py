import os
import json
import logging
from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "xoxb-your-token")
client = WebClient(token=SLACK_BOT_TOKEN)


@app.route("/slack/interactions", methods=["POST"])
def slack_interactions():
    # Slack requires a response within 3 seconds, so we always return 200 quickly.
    # See: https://api.slack.com/interactivity/handling#acknowledgment_response
    try:
        payload = json.loads(request.form["payload"])
    except (KeyError, json.JSONDecodeError) as e:
        logger.warning("Invalid interaction payload: %s", e)
        return "", 200

    if payload.get("type") != "block_actions":
        return "", 200

    action = payload["actions"][0]
    if action["action_id"] != "copy_url_button":
        return "", 200

    url = action.get("value", "")
    trigger_id = payload.get("trigger_id")
    if not trigger_id:
        logger.warning("No trigger_id in payload")
        return "", 200

    # Open modal with URL so user can copy (trigger_id is valid only for a short time)
    try:
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Copy URL"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "url_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "url_input",
                            "initial_value": url,
                            "multiline": False,
                        },
                        "label": {"type": "plain_text", "text": "Copy this URL"},
                    }
                ],
            },
        )
        logger.info("Modal opened for URL: %s", url[:50])
    except SlackApiError as e:
        logger.error("Slack API error opening modal: %s", e.response.get("error", str(e)))

    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
