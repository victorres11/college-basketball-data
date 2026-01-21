"""
Email notification utility for job completion using Resend.
"""
import os
import requests
from datetime import datetime


def send_job_completion_email(job_data):
    """
    Send email notification when a job completes using Resend.

    Args:
        job_data: Dictionary containing job information (status, url, team_name, etc.)
                  Can include 'notify_email' for dynamic recipient (e.g., from Google Sheets)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Get Resend API key from environment variables
    resend_api_key = os.environ.get('RESEND_API_KEY')

    # Build recipient list: always include NOTIFICATION_EMAIL, plus optional notify_email
    recipients = []

    # Always add the primary notification email (you)
    primary_email = os.environ.get('NOTIFICATION_EMAIL')
    if primary_email:
        recipients.append(primary_email)
        print(f"[EMAIL] Primary recipient (NOTIFICATION_EMAIL): {primary_email}")

    # Add the dynamic notify_email if provided and different from primary
    notify_email = job_data.get('notify_email')
    print(f"[EMAIL] notify_email from job_data: {notify_email}")
    if notify_email and notify_email not in recipients:
        recipients.append(notify_email)
        print(f"[EMAIL] Added notify_email to recipients: {notify_email}")
    elif notify_email and notify_email in recipients:
        print(f"[EMAIL] notify_email same as primary, not adding duplicate")
    else:
        print(f"[EMAIL] No notify_email provided in job_data")

    # Sender email - Resend provides a default sending domain for testing
    # Format: onboarding@resend.dev (for testing) or your verified domain
    sender_email = os.environ.get('RESEND_SENDER_EMAIL', 'onboarding@resend.dev')

    # Skip if email not configured
    if not resend_api_key:
        print("[EMAIL] Resend API key not configured (RESEND_API_KEY not set)")
        return False

    if not recipients:
        print("[EMAIL] No recipients (neither notify_email in job_data nor NOTIFICATION_EMAIL env var)")
        return False
    
    try:
        # Extract job information
        team_name = job_data.get('team_name', 'Unknown')
        season = job_data.get('season', 'Unknown')
        status = job_data.get('status', 'unknown')
        url = job_data.get('url', 'N/A')
        error = job_data.get('error')
        message = job_data.get('message', '')
        data_status = job_data.get('dataStatus', [])
        validation_errors = job_data.get('validationErrors')
        quality_report = job_data.get('qualityReport')

        # Build email subject with quality-aware tagging
        subject_prefix = ""
        if quality_report:
            max_severity = quality_report.get('max_severity', 'INFO')
            if max_severity == 'CRITICAL':
                subject_prefix = "[CRITICAL] "
            elif max_severity == 'ERROR':
                subject_prefix = "[ERRORS] "
        subject = f'{subject_prefix}CBB Data Generator - {team_name} ({season}) - {status.upper()}'
        
        # Build email body (HTML)
        html_body_lines = [
            f"<h2>CBB Data Generator - Job Completion</h2>",
            f"<p><strong>Team:</strong> {team_name}<br>",
            f"<strong>Season:</strong> {season}<br>",
            f"<strong>Status:</strong> <span style='color: {'green' if status == 'completed' else 'red' if status == 'failed' else 'orange'};'>{status.upper()}</span><br>",
            f"<strong>Message:</strong> {message}</p>",
        ]
        
        if url and url != 'N/A':
            html_body_lines.append(f"<p><strong>Generated URL:</strong> <a href='{url}'>{url}</a></p>")
        
        if error:
            html_body_lines.append(f"<p style='color: red;'><strong>Error:</strong> {error}</p>")

        if validation_errors:
            html_body_lines.append(f"<p style='color: orange;'><strong>Schema Validation Warnings:</strong></p>")
            html_body_lines.append(f"<pre style='background: #fff3cd; padding: 10px; overflow-x: auto;'>{validation_errors}</pre>")

        # Add Data Quality Report section
        if quality_report:
            checks_run = quality_report.get('checks_run', 0)
            checks_passed = quality_report.get('checks_passed', 0)
            pass_rate = quality_report.get('pass_rate', 100)
            max_severity = quality_report.get('max_severity', 'INFO')
            issues = quality_report.get('issues', [])

            # Determine bar color based on pass rate
            if pass_rate >= 90:
                bar_color = '#28a745'  # green
            elif pass_rate >= 70:
                bar_color = '#ffc107'  # yellow
            else:
                bar_color = '#dc3545'  # red

            # Determine header style based on max severity
            if max_severity == 'CRITICAL':
                header_style = "color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px;"
                header_icon = "🚨"
            elif max_severity == 'ERROR':
                header_style = "color: #856404; background: #fff3cd; padding: 10px; border-radius: 4px;"
                header_icon = "⚠️"
            else:
                header_style = ""
                header_icon = "✅" if pass_rate >= 90 else "📊"

            html_body_lines.append(f"<h3 style='{header_style}'>{header_icon} Data Quality Report</h3>")

            # Pass rate bar
            html_body_lines.append(f"""
            <div style="background: #e9ecef; border-radius: 4px; overflow: hidden; height: 24px; margin: 10px 0; position: relative;">
                <div style="background: {bar_color}; height: 100%; width: {pass_rate}%;"></div>
                <span style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-weight: bold;">{checks_passed}/{checks_run} checks passed ({pass_rate:.0f}%)</span>
            </div>
            """)

            # Issues table (if any)
            if issues:
                html_body_lines.append("<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; margin-top: 10px;'>")
                html_body_lines.append("<tr style='background: #f8f9fa;'><th>Severity</th><th>Check</th><th>Issue</th><th>Remediation</th></tr>")

                for issue in issues:
                    severity = issue.get('severity', 'WARNING')
                    validator = issue.get('validator', 'Unknown')
                    issue_message = issue.get('message', '')
                    remediation = issue.get('remediation', '')

                    # Severity styling
                    if severity == 'CRITICAL':
                        severity_style = "background: #dc3545; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px;"
                    elif severity == 'ERROR':
                        severity_style = "background: #ffc107; color: black; font-weight: bold; padding: 4px 8px; border-radius: 4px;"
                    else:
                        severity_style = "background: #17a2b8; color: white; padding: 4px 8px; border-radius: 4px;"

                    html_body_lines.append(f"""
                    <tr>
                        <td><span style='{severity_style}'>{severity}</span></td>
                        <td>{validator}</td>
                        <td>{issue_message}</td>
                        <td style='font-size: 0.9em; color: #666;'>{remediation if remediation else '-'}</td>
                    </tr>
                    """)

                html_body_lines.append("</table>")
            else:
                html_body_lines.append("<p style='color: #28a745;'>All data quality checks passed!</p>")

        if data_status:
            html_body_lines.append("<h3>Data Collection Status</h3>")
            html_body_lines.append("<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>")
            html_body_lines.append("<tr><th>Component</th><th>Status</th><th>Message</th></tr>")
            for item in data_status:
                name = item.get('name', 'Unknown')
                item_status = item.get('status', 'unknown')
                item_message = item.get('message', '')
                status_color = 'green' if item_status == 'success' else 'red' if item_status == 'failed' else 'orange'
                html_body_lines.append(
                    f"<tr>"
                    f"<td>{name}</td>"
                    f"<td style='color: {status_color};'>{item_status.upper()}</td>"
                    f"<td>{item_message}</td>"
                    f"</tr>"
                )
            html_body_lines.append("</table>")
        
        html_body_lines.append(f"<p><em>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>")
        
        html_body = "\n".join(html_body_lines)
        
        # Build plain text version
        text_body_lines = [
            f"Team: {team_name}",
            f"Season: {season}",
            f"Status: {status.upper()}",
            f"Message: {message}",
            "",
        ]
        
        if url and url != 'N/A':
            text_body_lines.append(f"Generated URL: {url}")
            text_body_lines.append("")
        
        if error:
            text_body_lines.append(f"Error: {error}")
            text_body_lines.append("")

        if validation_errors:
            text_body_lines.append("Schema Validation Warnings:")
            text_body_lines.append("-" * 40)
            text_body_lines.append(validation_errors)
            text_body_lines.append("")

        # Add Data Quality Report section (plain text)
        if quality_report:
            checks_run = quality_report.get('checks_run', 0)
            checks_passed = quality_report.get('checks_passed', 0)
            pass_rate = quality_report.get('pass_rate', 100)
            max_severity = quality_report.get('max_severity', 'INFO')
            issues = quality_report.get('issues', [])

            # Header with severity indicator
            if max_severity == 'CRITICAL':
                header = "DATA QUALITY REPORT [CRITICAL ISSUES]"
            elif max_severity == 'ERROR':
                header = "DATA QUALITY REPORT [ERRORS FOUND]"
            else:
                header = "DATA QUALITY REPORT"

            text_body_lines.append(header)
            text_body_lines.append("=" * 40)
            text_body_lines.append(f"Checks: {checks_passed}/{checks_run} passed ({pass_rate:.0f}%)")
            text_body_lines.append(f"Max Severity: {max_severity}")
            text_body_lines.append("")

            if issues:
                text_body_lines.append("Issues:")
                for issue in issues:
                    severity = issue.get('severity', 'WARNING')
                    validator = issue.get('validator', 'Unknown')
                    issue_message = issue.get('message', '')
                    remediation = issue.get('remediation', '')

                    severity_icon = "🚨" if severity == 'CRITICAL' else "⚠️" if severity == 'ERROR' else "⊘"
                    text_body_lines.append(f"{severity_icon} [{severity}] {validator}")
                    text_body_lines.append(f"   {issue_message}")
                    if remediation:
                        text_body_lines.append(f"   → Fix: {remediation}")
                    text_body_lines.append("")
            else:
                text_body_lines.append("All data quality checks passed!")
                text_body_lines.append("")

        if data_status:
            text_body_lines.append("Data Collection Status:")
            text_body_lines.append("-" * 40)
            for item in data_status:
                name = item.get('name', 'Unknown')
                item_status = item.get('status', 'unknown')
                item_message = item.get('message', '')
                status_icon = "✓" if item_status == 'success' else "✗" if item_status == 'failed' else "⊘"
                text_body_lines.append(f"{status_icon} {name}: {item_status.upper()}")
                if item_message:
                    text_body_lines.append(f"  → {item_message}")
            text_body_lines.append("")
        
        text_body_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        text_body = "\n".join(text_body_lines)
        
        # Send email via Resend API
        api_url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": sender_email,
            "to": recipients,
            "subject": subject,
            "html": html_body,
            "text": text_body
        }

        print(f"[EMAIL] Sending to {len(recipients)} recipient(s): {', '.join(recipients)}")
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"[EMAIL] Notification sent successfully from {sender_email} to {', '.join(recipients)}")
            print(f"[EMAIL] Resend response: {response.text}")
            return True
        else:
            print(f"[EMAIL] Failed to send notification. Status code: {response.status_code}")
            print(f"[EMAIL] Response: {response.text}")
            # Note: Resend free tier only allows sending to your own email.
            # To send to other addresses, verify a domain at https://resend.com/domains
            if response.status_code == 403 or "not allowed" in response.text.lower():
                print(f"[EMAIL] TIP: Resend free tier restricts recipients. Verify a domain to send to any email.")
            return False
        
    except Exception as e:
        print(f"[EMAIL] Failed to send notification: {e}")
        import traceback
        traceback.print_exc()
        return False

