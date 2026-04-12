

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

from telebot import types


class BroadcastSystem:
    def __init__(
        self,
        bot: Any,
        is_admin: Callable[[int], bool],
        get_all_users: Callable[[], List[Any]],
        safe_send: Callable[..., Any],
        log_admin_action: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.bot = bot
        self.is_admin = is_admin
        self.get_all_users = get_all_users
        self.safe_send = safe_send
        self.log_admin_action = log_admin_action

        # In-memory per-admin state
        self.states: Dict[int, Dict[str, Any]] = {}

    # ============================================================
    # State helpers
    # ============================================================

    def set_state(self, user_id: int, step: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.states[int(user_id)] = {
            "step": step,
            "data": data or {},
        }

    def get_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.states.get(int(user_id))

    def clear_state(self, user_id: int) -> None:
        self.states.pop(int(user_id), None)

    # ============================================================
    # UI helpers
    # ============================================================

    def main_menu(self) -> types.InlineKeyboardMarkup:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📝 Text Broadcast", callback_data="advbrod_type_text"),
            types.InlineKeyboardButton("🖼 Photo Broadcast", callback_data="advbrod_type_photo"),
        )
        markup.add(
            types.InlineKeyboardButton("🎬 Video Broadcast", callback_data="advbrod_type_video"),
            types.InlineKeyboardButton("📄 Document Broadcast", callback_data="advbrod_type_document"),
        )
        markup.add(
            types.InlineKeyboardButton("🎞 Animation Broadcast", callback_data="advbrod_type_animation"),
            types.InlineKeyboardButton("🎵 Audio Broadcast", callback_data="advbrod_type_audio"),
        )
        markup.add(
            types.InlineKeyboardButton("🎤 Voice Broadcast", callback_data="advbrod_type_voice"),
            types.InlineKeyboardButton("🙂 Sticker Broadcast", callback_data="advbrod_type_sticker"),
        )
        markup.add(
            types.InlineKeyboardButton("📤 Forward / Copy Existing", callback_data="advbrod_type_copy")
        )
        markup.add(
            types.InlineKeyboardButton("❌ Cancel", callback_data="advbrod_cancel")
        )
        return markup

    def buttons_menu(self) -> types.InlineKeyboardMarkup:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Add Buttons", callback_data="advbrod_buttons_yes"),
            types.InlineKeyboardButton("⏭ Skip Buttons", callback_data="advbrod_buttons_no"),
        )
        markup.add(
            types.InlineKeyboardButton("❌ Cancel", callback_data="advbrod_cancel")
        )
        return markup

    def preview_menu(self) -> types.InlineKeyboardMarkup:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Send Broadcast", callback_data="advbrod_send"),
            types.InlineKeyboardButton("✏️ Edit Buttons", callback_data="advbrod_edit_buttons"),
        )
        markup.add(
            types.InlineKeyboardButton("🔁 Restart", callback_data="advbrod_restart"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="advbrod_cancel"),
        )
        return markup

    def parse_buttons(self, raw_text: str) -> Optional[types.InlineKeyboardMarkup]:
        """
        Supported format: JSON array of rows
        Example:
        [
          [{"text":"Join Channel","url":"https://t.me/example"}],
          [{"text":"Open Bot","url":"https://t.me/yourbot"}]
        ]

        Or callback button:
        [
          [{"text":"Check","callback_data":"check"}]
        ]
        """
        raw_text = (raw_text or "").strip()
        if not raw_text:
            return None

        parsed = json.loads(raw_text)
        if not isinstance(parsed, list):
            raise ValueError("Buttons JSON must be a list of rows.")

        markup = types.InlineKeyboardMarkup()
        for row in parsed:
            if not isinstance(row, list):
                raise ValueError("Each row must be a list.")
            btn_row = []
            for item in row:
                if not isinstance(item, dict):
                    raise ValueError("Each button must be an object.")
                text = item.get("text", "").strip()
                url = item.get("url")
                callback_data = item.get("callback_data")
                if not text:
                    raise ValueError("Each button needs text.")
                if url:
                    btn_row.append(types.InlineKeyboardButton(text, url=url))
                elif callback_data:
                    btn_row.append(types.InlineKeyboardButton(text, callback_data=callback_data))
                else:
                    raise ValueError("Each button needs either url or callback_data.")
            if btn_row:
                markup.row(*btn_row)
        return markup

    # ============================================================
    # Message building helpers
    # ============================================================

    def collect_target_users(self) -> List[int]:
        users = self.get_all_users() or []
        user_ids: List[int] = []
        for u in users:
            try:
                if isinstance(u, dict):
                    uid = int(u.get("user_id"))
                else:
                    uid = int(u["user_id"])
                user_ids.append(uid)
            except Exception:
                continue
        return user_ids

    def build_preview_text(self, data: Dict[str, Any], total_users: int) -> str:
        btype = data.get("broadcast_type", "unknown")
        body = data.get("text") or data.get("caption") or "(no text)"
        if len(body) > 800:
            body = body[:800] + "\n\n...truncated in preview..."

        return (
            f"🚀 <b>Advanced Broadcast Preview</b>\n\n"
            f"<b>Type:</b> {btype}\n"
            f"<b>Total users:</b> {total_users}\n"
            f"<b>Buttons:</b> {'Yes' if data.get('buttons_json') else 'No'}\n\n"
            f"<b>Preview text/caption:</b>\n{body}"
        )

    def send_preview(self, chat_id: int, data: Dict[str, Any]) -> None:
        total_users = len(self.collect_target_users())
        markup = None
        try:
            markup = self.parse_buttons(data.get("buttons_json", ""))
        except Exception:
            markup = None

        preview_text = self.build_preview_text(data, total_users)
        btype = data.get("broadcast_type")

        if btype == "text":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.safe_send(chat_id, data.get("text", "(empty)"), reply_markup=markup)

        elif btype == "photo":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_photo(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "video":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_video(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "document":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_document(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "animation":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_animation(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "audio":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_audio(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "voice":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_voice(
                chat_id,
                data["file_id"],
                caption=data.get("caption", ""),
                parse_mode="HTML",
                reply_markup=markup,
            )

        elif btype == "sticker":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.send_sticker(chat_id, data["file_id"])

        elif btype == "copy":
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())
            self.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=data["source_chat_id"],
                message_id=data["source_message_id"],
                reply_markup=markup,
            )
        else:
            self.safe_send(chat_id, preview_text, reply_markup=self.preview_menu())

    # ============================================================
    # Broadcast sending engine
    # ============================================================

    def send_to_one(self, user_id: int, data: Dict[str, Any]) -> bool:
        markup = None
        try:
            markup = self.parse_buttons(data.get("buttons_json", ""))
        except Exception:
            markup = None

        btype = data.get("broadcast_type")

        try:
            if btype == "text":
                self.bot.send_message(
                    user_id,
                    data.get("text", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                    disable_web_page_preview=False,
                )

            elif btype == "photo":
                self.bot.send_photo(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "video":
                self.bot.send_video(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "document":
                self.bot.send_document(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "animation":
                self.bot.send_animation(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "audio":
                self.bot.send_audio(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "voice":
                self.bot.send_voice(
                    user_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            elif btype == "sticker":
                self.bot.send_sticker(user_id, data["file_id"])

            elif btype == "copy":
                self.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=data["source_chat_id"],
                    message_id=data["source_message_id"],
                    reply_markup=markup,
                )
            else:
                return False

            return True
        except Exception:
            return False

    def execute_broadcast(self, admin_id: int, data: Dict[str, Any]) -> Dict[str, int]:
        user_ids = self.collect_target_users()
        sent = 0
        failed = 0

        start_time = time.time()

        for uid in user_ids:
            ok = self.send_to_one(uid, data)
            if ok:
                sent += 1
            else:
                failed += 1
            time.sleep(0.03)

        duration = round(time.time() - start_time, 2)

        if self.log_admin_action:
            try:
                self.log_admin_action(
                    admin_id,
                    "advanced_broadcast",
                    f"type={data.get('broadcast_type')} sent={sent} failed={failed} duration={duration}s"
                )
            except Exception:
                pass

        return {
            "total": len(user_ids),
            "sent": sent,
            "failed": failed,
            "duration": duration,
        }

    # ============================================================
    # Register handlers
    # ============================================================

    def register_handlers(self) -> None:
        @self.bot.message_handler(commands=["advbrod"])
        def open_advanced_broadcast(message: Any) -> None:
            user_id = message.from_user.id
            if not self.is_admin(user_id):
                self.safe_send(message.chat.id, "❌ Access denied")
                return

            self.clear_state(user_id)
            self.safe_send(
                message.chat.id,
                "🚀 <b>Advanced Broadcast Panel</b>\n\n"
                "Choose the broadcast type.\n\n"
                "<b>Supported:</b>\n"
                "• text\n"
                "• photo\n"
                "• video\n"
                "• document\n"
                "• animation\n"
                "• audio\n"
                "• voice\n"
                "• sticker\n"
                "• forward/copy existing message\n\n"
                "HTML formatting and premium emoji tags are supported.",
                reply_markup=self.main_menu()
            )

        @self.bot.callback_query_handler(func=lambda call: isinstance(call.data, str) and call.data.startswith("advbrod_"))
        def advbrod_callbacks(call: Any) -> None:
            user_id = call.from_user.id
            if not self.is_admin(user_id):
                self.safe_answer(call, "Access denied", True)
                return

            data = call.data
            self.safe_answer(call)

            if data == "advbrod_cancel":
                self.clear_state(user_id)
                self.safe_send(call.message.chat.id, "❌ Broadcast cancelled.")
                return

            if data == "advbrod_restart":
                self.clear_state(user_id)
                self.safe_send(
                    call.message.chat.id,
                    "🔁 Restarted. Choose the broadcast type again.",
                    reply_markup=self.main_menu()
                )
                return

            if data.startswith("advbrod_type_"):
                btype = data.replace("advbrod_type_", "", 1)
                self.set_state(user_id, "await_primary_content", {"broadcast_type": btype})

                prompts = {
                    "text": (
                        "📝 <b>Send broadcast text now</b>\n\n"
                        "You can use:\n"
                        "• HTML formatting\n"
                        "• premium emoji tags\n"
                        "• long messages\n\n"
                        "Example:\n"
                        "&lt;b&gt;Big Update&lt;/b&gt;"
                    ),
                    "photo": "🖼 <b>Send the photo now</b>\n\nCaption allowed.",
                    "video": "🎬 <b>Send the video now</b>\n\nCaption allowed.",
                    "document": "📄 <b>Send the document now</b>\n\nCaption allowed.",
                    "animation": "🎞 <b>Send the GIF/animation now</b>\n\nCaption allowed.",
                    "audio": "🎵 <b>Send the audio now</b>\n\nCaption allowed.",
                    "voice": "🎤 <b>Send the voice now</b>\n\nCaption allowed.",
                    "sticker": "🙂 <b>Send the sticker now</b>",
                    "copy": (
                        "📤 <b>Forward the source message to me now</b>\n\n"
                        "I will save it and later copy it to all users."
                    ),
                }

                self.safe_send(call.message.chat.id, prompts.get(btype, "Send content now."))
                return

            if data == "advbrod_buttons_yes":
                state = self.get_state(user_id)
                if not state:
                    self.safe_send(call.message.chat.id, "❌ No active broadcast.")
                    return

                state["step"] = "await_buttons_json"
                self.safe_send(
                    call.message.chat.id,
                    "➕ <b>Send buttons JSON now</b>\n\n"
                    "Example:\n"
                    "<code>[\n"
                    '  [{"text":"Join Channel","url":"https://t.me/example"}],\n'
                    '  [{"text":"Open Bot","url":"https://t.me/yourbot"}]\n'
                    "]</code>"
                )
                return

            if data == "advbrod_buttons_no":
                state = self.get_state(user_id)
                if not state:
                    self.safe_send(call.message.chat.id, "❌ No active broadcast.")
                    return

                state["data"]["buttons_json"] = ""
                state["step"] = "ready_preview"
                self.send_preview(call.message.chat.id, state["data"])
                return

            if data == "advbrod_edit_buttons":
                state = self.get_state(user_id)
                if not state:
                    self.safe_send(call.message.chat.id, "❌ No active broadcast.")
                    return
                state["step"] = "await_buttons_json"
                self.safe_send(
                    call.message.chat.id,
                    "✏️ <b>Send new buttons JSON</b>\n\n"
                    "Or send:\n"
                    "<code>[]</code>\n"
                    "to remove buttons."
                )
                return

            if data == "advbrod_send":
                state = self.get_state(user_id)
                if not state:
                    self.safe_send(call.message.chat.id, "❌ No active broadcast.")
                    return

                self.safe_send(call.message.chat.id, "🚀 Sending advanced broadcast... please wait.")
                result = self.execute_broadcast(user_id, state["data"])
                self.clear_state(user_id)

                self.safe_send(
                    call.message.chat.id,
                    f"✅ <b>Broadcast Finished</b>\n\n"
                    f"• Total users: <b>{result['total']}</b>\n"
                    f"• Sent: <b>{result['sent']}</b>\n"
                    f"• Failed: <b>{result['failed']}</b>\n"
                    f"• Duration: <b>{result['duration']}s</b>"
                )
                return

        @self.bot.message_handler(
            func=lambda m: self.is_admin(m.from_user.id) and self.get_state(m.from_user.id) is not None,
            content_types=["text", "photo", "video", "document", "animation", "audio", "voice", "sticker"]
        )
        def advbrod_state_handler(message: Any) -> None:
            user_id = message.from_user.id
            state = self.get_state(user_id)
            if not state:
                return

            step = state["step"]
            data = state["data"]
            chat_id = message.chat.id
            btype = data.get("broadcast_type")

            if step == "await_primary_content":
                if btype == "text":
                    if message.content_type != "text":
                        self.safe_send(chat_id, "❌ Send plain text for text broadcast.")
                        return
                    data["text"] = message.text or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(
                        chat_id,
                        "Text saved ✅\n\nDo you want to add inline buttons?",
                        reply_markup=self.buttons_menu()
                    )
                    return

                if btype == "photo":
                    if message.content_type != "photo":
                        self.safe_send(chat_id, "❌ Send a photo.")
                        return
                    data["file_id"] = message.photo[-1].file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Photo saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "video":
                    if message.content_type != "video":
                        self.safe_send(chat_id, "❌ Send a video.")
                        return
                    data["file_id"] = message.video.file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Video saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "document":
                    if message.content_type != "document":
                        self.safe_send(chat_id, "❌ Send a document.")
                        return
                    data["file_id"] = message.document.file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Document saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "animation":
                    if message.content_type != "animation":
                        self.safe_send(chat_id, "❌ Send an animation/GIF.")
                        return
                    data["file_id"] = message.animation.file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Animation saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "audio":
                    if message.content_type != "audio":
                        self.safe_send(chat_id, "❌ Send audio.")
                        return
                    data["file_id"] = message.audio.file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Audio saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "voice":
                    if message.content_type != "voice":
                        self.safe_send(chat_id, "❌ Send a voice note.")
                        return
                    data["file_id"] = message.voice.file_id
                    data["caption"] = message.caption or ""
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Voice saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "sticker":
                    if message.content_type != "sticker":
                        self.safe_send(chat_id, "❌ Send a sticker.")
                        return
                    data["file_id"] = message.sticker.file_id
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Sticker saved ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

                if btype == "copy":
                    data["source_chat_id"] = message.chat.id
                    data["source_message_id"] = message.message_id
                    self.set_state(user_id, "await_buttons_choice", data)
                    self.safe_send(chat_id, "Message saved for copy broadcast ✅\n\nAdd buttons?", reply_markup=self.buttons_menu())
                    return

            if step == "await_buttons_json":
                if message.content_type != "text":
                    self.safe_send(chat_id, "❌ Send buttons as text JSON.")
                    return

                raw = message.text or ""
                try:
                    markup = self.parse_buttons(raw)
                    data["buttons_json"] = raw if raw.strip() != "[]" else ""
                    self.set_state(user_id, "ready_preview", data)
                    self.safe_send(chat_id, "✅ Buttons saved.")
                    self.send_preview(chat_id, data)
                except Exception as e:
                    self.safe_send(
                        chat_id,
                        f"❌ Invalid buttons JSON\n\n<b>Error:</b> <code>{str(e)}</code>\n\nTry again."
                    )
                return
