from __future__ import annotations

from typing import Any, Callable


class AdminHelpSystem:
    def __init__(
        self,
        bot: Any,
        is_admin: Callable[[int], bool],
        safe_send: Callable[..., Any],
        pe: Callable[[str], str],
    ) -> None:
        self.bot = bot
        self.is_admin = is_admin
        self.safe_send = safe_send
        self.pe = pe

    def build_help_text(self) -> str:
        return (
            f"{self.pe('admin')} <b>Admin Help Center</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{self.pe('database')} <b>Database Commands</b>\n"
            f"{self.pe('arrow')} <code>/getdb</code> — Download current bot database\n"
            f"{self.pe('arrow')} <code>/uploaddb</code> — Upload and merge old database\n\n"

            f"{self.pe('megaphone')} <b>Broadcast Commands</b>\n"
            f"{self.pe('arrow')} <code>/advbrod</code> — Open advanced broadcast panel\n\n"

            f"{self.pe('shield')} <b>Security / Anti-Cheat</b>\n"
            f"{self.pe('arrow')} <code>/anticheat</code> — Open anti-cheat admin panel\n\n"

            f"{self.pe('calendar')} <b>Withdrawal Limit</b>\n"
            f"{self.pe('arrow')} <code>/withdrawlimit</code> — Show current daily withdrawal limit\n"
            f"{self.pe('arrow')} <code>/setwithdrawlimit 2</code> — Set daily withdrawal limit\n\n"

            f"{self.pe('gear')} <b>Main Admin Panel</b>\n"
            f"{self.pe('arrow')} Use <b>👑 Admin Panel</b> button for dashboard, settings, withdrawals, tasks, gifts, admins, and user tools\n\n"

            f"{self.pe('bulb')} <b>Notes</b>\n"
            f"{self.pe('arrow')} All commands here are <b>admin-only</b>\n"
            f"{self.pe('arrow')} Keep bot token and Railway variables private\n"
            f"{self.pe('arrow')} Rotate token immediately if it was exposed\n\n"

            f"{self.pe('sparkle')} <b>Quick Tip:</b> Use <code>/adminhelp</code> anytime to open this list again."
        )

    def register_handlers(self) -> None:
        @self.bot.message_handler(commands=["adminhelp"])
        def admin_help_command(message: Any) -> None:
            if not self.is_admin(message.from_user.id):
                self.safe_send(message.chat.id, "❌ Access denied")
                return

            self.safe_send(message.chat.id, self.build_help_text())
