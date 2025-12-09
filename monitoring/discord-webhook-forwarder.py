#!/usr/bin/env python3
"""
Discord Webhook Forwarder for Alertmanager
Converts Alertmanager webhook format to Discord-friendly embeds
"""

from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Discord webhook URL from environment variable
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Color codes for different severities
SEVERITY_COLORS = {
    'critical': 0xFF0000,  # Red
    'warning': 0xFFA500,   # Orange
    'info': 0x0099FF,      # Blue
    'resolved': 0x00FF00,  # Green
}

# Emoji for different severities
SEVERITY_EMOJI = {
    'critical': '🚨',
    'warning': '⚠️',
    'info': '📊',
    'resolved': '✅',
}

def format_discord_message(alert_data):
    """Convert Alertmanager payload to Discord embed format"""
    
    alerts = alert_data.get('alerts', [])
    if not alerts:
        return None
    
    embeds = []
    
    for alert in alerts[:10]:  # Limit to 10 alerts per message
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        status = alert.get('status', 'firing')
        
        severity = labels.get('severity', 'info')
        if status == 'resolved':
            color = SEVERITY_COLORS['resolved']
            emoji = SEVERITY_EMOJI['resolved']
            title_prefix = "RESOLVED"
        else:
            color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS['info'])
            emoji = SEVERITY_EMOJI.get(severity, '❓')
            title_prefix = severity.upper()
        
        # Build embed
        embed = {
            'title': f"{emoji} {title_prefix}: {annotations.get('summary', labels.get('alertname', 'Unknown Alert'))}",
            'description': annotations.get('description', 'No description provided'),
            'color': color,
            'fields': [],
            'footer': {
                'text': f"TailorJob Monitoring • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
        }
        
        # Add action field if provided
        if 'action' in annotations:
            embed['fields'].append({
                'name': '🔧 Action Required',
                'value': annotations['action'],
                'inline': False
            })
        
        # Add relevant labels
        if 'job' in labels:
            embed['fields'].append({
                'name': 'Service',
                'value': labels['job'],
                'inline': True
            })
        
        if 'endpoint' in labels:
            embed['fields'].append({
                'name': 'Endpoint',
                'value': labels['endpoint'],
                'inline': True
            })
        
        # Add alert metadata
        if status == 'firing':
            starts_at = alert.get('startsAt', '')
            if starts_at:
                embed['fields'].append({
                    'name': 'Started',
                    'value': starts_at.split('.')[0].replace('T', ' '),
                    'inline': True
                })
        else:
            ends_at = alert.get('endsAt', '')
            if ends_at:
                embed['fields'].append({
                    'name': 'Resolved',
                    'value': ends_at.split('.')[0].replace('T', ' '),
                    'inline': True
                })
        
        embeds.append(embed)
    
    # Prepare Discord message
    message = {
        'embeds': embeds
    }
    
    # Add @everyone mention for critical alerts
    if any(a.get('labels', {}).get('severity') == 'critical' and a.get('status') == 'firing' 
           for a in alerts):
        message['content'] = '@everyone **CRITICAL ALERT**'
    
    return message

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive Alertmanager webhook and forward to Discord"""
    
    if not DISCORD_WEBHOOK_URL:
        return jsonify({'error': 'Discord webhook URL not configured'}), 500
    
    try:
        alert_data = request.json
        
        if not alert_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Convert to Discord format
        discord_message = format_discord_message(alert_data)
        
        if not discord_message:
            return jsonify({'error': 'No alerts to send'}), 400
        
        # Send to Discord
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=discord_message,
            timeout=10
        )
        
        if response.status_code not in [200, 204]:
            print(f"Discord API error: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to send to Discord'}), 500
        
        return jsonify({'success': True, 'alerts_sent': len(discord_message['embeds'])}), 200
    
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'discord_configured': bool(DISCORD_WEBHOOK_URL)
    }), 200

if __name__ == '__main__':
    if not DISCORD_WEBHOOK_URL:
        print("WARNING: DISCORD_WEBHOOK_URL not set")
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)