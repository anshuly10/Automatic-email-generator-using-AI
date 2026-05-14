# main.py
# AI Gmail Agent — interactive CLI

import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import print as rprint
import questionary

from auth import get_credentials
from drive import find_file, download_file
from drafter import draft_email
from gmail import create_draft, send_email

load_dotenv()
console = Console()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def banner():
    console.clear()
    console.print(Panel(
        Text("AI Gmail Agent  🤖 📧", justify="center", style="bold cyan"),
        subtitle="[dim]Powered by llama + Gmail + Google Drive[/dim]",
        border_style="cyan",
    ))

def section(title: str):
    console.print(f"\n[bold yellow]▶ {title}[/bold yellow]")
    console.print(Rule(style="dim"))

def success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")

def warn(msg: str):
    console.print(f"[bold yellow]⚠[/bold yellow]  {msg}")

def error(msg: str):
    console.print(f"[bold red]✗[/bold red] {msg}")

def validate_emails(val: str):
    import re
    emails = [e.strip() for e in val.split(",") if e.strip()]
    if not emails:
        return "Enter at least one email address."
    invalid = [e for e in emails if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", e)]
    if invalid:
        return f"Invalid email(s): {', '.join(invalid)}"
    return True


# ─── Main flow ────────────────────────────────────────────────────────────────

def main():
    banner()

    # 1. Authenticate
    section("Google Authentication")
    with console.status("Connecting to Google..."):
        try:
            creds = get_credentials()
            success("Google authenticated")
        except Exception as e:
            error(f"Authentication failed: {e}")
            console.print("[dim]Run [bold]python auth.py[/bold] first to set up Google OAuth.[/dim]")
            sys.exit(1)

    # 2. Recipients
    section("Recipients")
    recipient_input = questionary.text(
        "Enter recipient email(s), comma-separated:",
        validate=validate_emails,
    ).ask()
    if not recipient_input:
        sys.exit(0)

    recipients = [e.strip() for e in recipient_input.split(",") if e.strip()]
    success(f"Recipients: {', '.join(recipients)}")

    # 3. Email details
    section("Email Details")
    purpose = questionary.text(
        "Subject / purpose of the email:",
        validate=lambda v: True if v.strip() else "Please enter a subject.",
    ).ask()

    context = questionary.text(
        "Key points / what should the email say:",
        validate=lambda v: True if v.strip() else "Please provide some context.",
    ).ask()

    tone = questionary.select(
        "Tone:",
        choices=["Professional", "Friendly", "Formal", "Concise", "Persuasive"],
        default="Professional",
    ).ask()

    sender_name = questionary.text(
        "Your name (for sign-off, optional):",
    ).ask() or ""

    # 4. Google Drive attachment
    section("Attachment (Google Drive)")
    want_attachment = questionary.confirm(
        "Attach a file from Google Drive?", default=True
    ).ask()

    attachment = None

    if want_attachment:
        file_path = questionary.text(
            "File name or path in Google Drive (e.g. Reports/Q3-2025.pdf):",
            validate=lambda v: True if v.strip() else "Enter a file name.",
        ).ask()

        with console.status(f'Searching Google Drive for "{file_path}"...'):
            try:
                file_info = find_file(creds, file_path)
                if not file_info:
                    warn(f'File not found: "{file_path}" — continuing without attachment.')
                else:
                    console.print(f"  Found: [cyan]{file_info['name']}[/cyan] ({file_info['mimeType']})")
            except Exception as e:
                warn(f"Drive search error: {e} — continuing without attachment.")
                file_info = None

        if file_info:
            with console.status(f"Downloading {file_info['name']}..."):
                try:
                    data, actual_mime = download_file(creds, file_info["id"], file_info["mimeType"])
                    attachment = {
                        "name": file_info["name"],
                        "mime_type": actual_mime,
                        "data": data,
                    }
                    success(f"Attachment ready: {file_info['name']} ({len(data) / 1024:.1f} KB)")
                except Exception as e:
                    warn(f"Download failed: {e} — continuing without attachment.")

    # 5. Draft with Claude
    section("AI Drafting")
    with console.status("Claude is drafting your email..."):
        try:
            draft = draft_email(
                recipients=recipients,
                purpose=purpose,
                context=context,
                tone=tone.lower(),
                sender_name=sender_name,
                attachment_name=attachment["name"] if attachment else "",
            )
            success("Email drafted!")
        except Exception as e:
            error(f"Drafting failed: {e}")
            sys.exit(1)

    # 6. Preview
    console.print()
    console.print(Rule(style="bold white"))
    console.print("[bold]📧  DRAFT PREVIEW[/bold]")
    console.print(Rule(style="bold white"))
    console.print(f"[dim]To:[/dim]      {', '.join(recipients)}")
    console.print(f"[dim]Subject:[/dim] {draft['subject']}")
    if attachment:
        console.print(f"[dim]Attach:[/dim]  [cyan]📎 {attachment['name']}[/cyan]")
    console.print(Rule(style="dim"))
    console.print(draft["body"])
    console.print(Rule(style="bold white"))

    # 7. Action
    section("What would you like to do?")
    action = questionary.select(
        "Choose an action:",
        choices=[
            questionary.Choice("📬  Save as Gmail Draft (review before sending)", value="draft"),
            questionary.Choice("🚀  Send immediately via Gmail", value="send"),
            questionary.Choice("✏️   Re-draft (change instructions)", value="redraft"),
            questionary.Choice("❌  Cancel", value="cancel"),
        ],
    ).ask()

    if action == "cancel" or action is None:
        console.print("[dim]\nCancelled. No email was sent.[/dim]")
        sys.exit(0)

    if action == "redraft":
        console.print("[yellow]\nRestarting...[/yellow]")
        return main()

    # 8. Save draft or send
    with console.status("Saving draft..." if action == "draft" else "Sending email..."):
        try:
            if action == "draft":
                result = create_draft(
                    creds,
                    to=recipients,
                    subject=draft["subject"],
                    body=draft["body"],
                    attachment=attachment,
                )
                success(f"Draft saved! ID: {result['id']}")
                console.print("[dim]Open Gmail → Drafts to review and send.[/dim]")
            else:
                result = send_email(
                    creds,
                    to=recipients,
                    subject=draft["subject"],
                    body=draft["body"],
                    attachment=attachment,
                )
                success(f"Email sent! Message ID: {result['id']}")
        except Exception as e:
            error(f"Failed: {e}")
            if "insufficient" in str(e).lower():
                console.print(
                    "[yellow]⚠  Permission error. Delete token.json and run "
                    "[bold]python auth.py[/bold] again.[/yellow]"
                )
            sys.exit(1)

    # 9. Loop?
    again = questionary.confirm("Send another email?", default=False).ask()
    if again:
        return main()

    console.print("\n[bold cyan]✨ Done! Goodbye.[/bold cyan]\n")


if __name__ == "__main__":
    main()
