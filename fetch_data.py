#!/usr/bin/env python3
"""
Script pour récupérer les données HubSpot et générer le rapport.
S'exécute automatiquement tous les jours à 17h30 via GitHub Actions.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
HUBSPOT_TOKEN = os.environ.get('HUBSPOT_TOKEN')
PORTAL_ID = "146716340"
RAPHAEL_CONTACT_ID = "442451012837"
RAPHAEL_OWNER_ID = "29926733"  # Owner ID de Raphaël dans HubSpot (tasks, meetings)
RAPHAEL_OWNER_ID_CALLS = "29974224"  # Owner ID de Raphaël pour les appels
COMPANY_13_YEARS_ID = "234376298682"
BASE_URL = "https://api.hubapi.com"
SESSION_GAP_MINUTES = 30

def fetch_engagements():
    """Récupère tous les engagements de Raphaël depuis le début de la période."""
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Date de début : lundi dernier
    today = datetime.now()
    days_since_monday = (today.weekday() - 0) % 7
    if days_since_monday == 0 and today.hour < 17:
        days_since_monday = 7
    monday = today - timedelta(days=days_since_monday)
    start_timestamp = int(monday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

    all_engagements = []
    sequence_emails_excluded = 0
    offset = 0
    has_more = True

    print(f"📅 Récupération des données depuis le {monday.strftime('%d/%m/%Y')}...")

    while has_more:
        url = f"{BASE_URL}/engagements/v1/engagements/paged"
        params = {
            'limit': 100,
            'offset': offset
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Filtrer les engagements de Raphaël après la date de début
        for eng in data.get('results', []):
            engagement = eng.get('engagement', {})
            eng_type = engagement.get('type')

            # Utiliser createdAt pour filtrer par date de CRÉATION, pas date d'échéance/prévue
            created_at = engagement.get('createdAt', 0)
            if created_at < start_timestamp:
                continue

            # Vérifier que c'est bien un engagement de Raphaël
            owner_id = engagement.get('ownerId')
            associations = eng.get('associations', {})
            contact_ids = associations.get('contactIds', [])
            company_ids = associations.get('companyIds', [])

            # Filtrer: owner ID de Raphaël (2 IDs) OU Raphaël dans les contacts OU company 13 Years
            is_raphael_owner = str(owner_id) in [str(RAPHAEL_OWNER_ID), str(RAPHAEL_OWNER_ID_CALLS)]
            is_raphael_in_contacts = RAPHAEL_CONTACT_ID in [str(cid) for cid in contact_ids]
            is_13years_company = COMPANY_13_YEARS_ID in [str(cid) for cid in company_ids]

            if is_raphael_owner or is_raphael_in_contacts or is_13years_company:
                # Exclure les emails de séquence
                if eng_type == 'EMAIL':
                    metadata = eng.get('metadata', {})
                    if metadata.get('sequenceId'):
                        sequence_emails_excluded += 1
                        continue

                all_engagements.append(eng)

        has_more = data.get('hasMore', False)
        offset = data.get('offset', 0)

        if has_more:
            print(f"  ⏳ Récupéré {len(all_engagements)} engagements, continuation...")

    print(f"✅ Total récupéré : {len(all_engagements)} engagements")
    if sequence_emails_excluded > 0:
        print(f"📧 Emails de séquence exclus : {sequence_emails_excluded}")
    return all_engagements

def format_engagements(engagements):
    """Formate les engagements pour le dashboard."""
    formatted = []

    for eng_data in engagements:
        engagement = eng_data.get('engagement', {})
        metadata = eng_data.get('metadata', {})
        associations = eng_data.get('associations', {})

        eng_type = engagement.get('type')
        # Utiliser createdAt = date de CRÉATION de l'engagement (quand Raphaël a fait l'action)
        # Pas timestamp qui peut être une date future (échéance tâche, date réunion prévue)
        created_at = engagement.get('createdAt', 0)
        dt = datetime.fromtimestamp(created_at / 1000)

        # Construire l'URL HubSpot correcte
        contact_ids = associations.get('contactIds', [])
        # Trouver un contact autre que Raphaël pour le lien
        other_contacts = [cid for cid in contact_ids if str(cid) != RAPHAEL_CONTACT_ID]
        contact_id = other_contacts[0] if other_contacts else (contact_ids[0] if contact_ids else RAPHAEL_CONTACT_ID)

        url = f"https://app-eu1.hubspot.com/contacts/{PORTAL_ID}/contact/{contact_id}/?engagement={engagement.get('id')}"

        formatted_eng = {
            'id': str(engagement.get('id')),
            'type': eng_type,
            'timestamp': created_at,  # Date de création de l'action
            'date': dt.strftime('%Y-%m-%d'),
            'datetime': dt.strftime('%d/%m/%Y %H:%M'),
            'time': dt.strftime('%H:%M'),
            'portal_id': PORTAL_ID,
            'url': url
        }

        # Détails selon le type
        if eng_type == 'EMAIL':
            formatted_eng.update({
                'subject': metadata.get('subject', ''),
                'to': metadata.get('to', []),
                'from': metadata.get('from', {}).get('email', ''),
                'preview': metadata.get('text', '')[:200],
                'status': metadata.get('status', '')
            })
        elif eng_type == 'CALL':
            formatted_eng.update({
                'title': metadata.get('title', ''),
                'body': metadata.get('body', ''),
                'status': metadata.get('status', ''),
                'duration': metadata.get('durationMilliseconds', 0),
                'disposition': metadata.get('disposition', ''),
                'toNumber': metadata.get('toNumber', ''),
                'fromNumber': metadata.get('fromNumber', '')
            })
        elif eng_type == 'TASK':
            formatted_eng.update({
                'subject': metadata.get('subject', ''),
                'body': metadata.get('body', ''),
                'status': metadata.get('status', ''),
                'priority': metadata.get('priority', ''),
                'taskType': metadata.get('taskType', '')
            })
        elif eng_type == 'NOTE':
            formatted_eng.update({
                'body': metadata.get('body', ''),
                'preview': (metadata.get('body', '') or '')[:200]
            })
        elif eng_type == 'MEETING':
            formatted_eng.update({
                'title': metadata.get('title', ''),
                'body': metadata.get('body', ''),
                'startTime': metadata.get('startTime', ''),
                'endTime': metadata.get('endTime', ''),
                'location': metadata.get('location', '')
            })
        else:
            # Pour tout autre type, capturer les métadonnées de base
            formatted_eng.update({
                'title': metadata.get('title', ''),
                'body': metadata.get('body', ''),
                'subject': metadata.get('subject', '')
            })

        formatted.append(formatted_eng)

    # Trier par timestamp décroissant
    formatted.sort(key=lambda x: x['timestamp'], reverse=True)
    return formatted

def calculate_work_sessions(engagements):
    """Calcule les sessions de travail avec un seuil de 30 minutes."""
    # Grouper par date
    by_date = defaultdict(list)
    for eng in engagements:
        by_date[eng['date']].append(eng)

    work_analysis = []

    for date in sorted(by_date.keys()):
        day_activities = by_date[date]
        timestamps = [datetime.fromtimestamp(a['timestamp'] / 1000) for a in day_activities]
        timestamps.sort()

        if not timestamps:
            continue

        sessions = []
        session_start = timestamps[0]
        session_end = timestamps[0]
        session_actions = 1

        for i in range(1, len(timestamps)):
            diff_minutes = (timestamps[i] - session_end).total_seconds() / 60

            if diff_minutes > SESSION_GAP_MINUTES:
                # Fin de session
                duration_min = (session_end - session_start).total_seconds() / 60
                sessions.append({
                    'debut': session_start.strftime('%H:%M'),
                    'fin': session_end.strftime('%H:%M'),
                    'actions': session_actions,
                    'dureeMin': int(duration_min)
                })

                # Nouvelle session
                session_start = timestamps[i]
                session_end = timestamps[i]
                session_actions = 1
            else:
                session_end = timestamps[i]
                session_actions += 1

        # Dernière session
        duration_min = (session_end - session_start).total_seconds() / 60
        sessions.append({
            'debut': session_start.strftime('%H:%M'),
            'fin': session_end.strftime('%H:%M'),
            'actions': session_actions,
            'dureeMin': int(duration_min)
        })

        total_duration = sum(s['dureeMin'] for s in sessions) / 60

        work_analysis.append({
            'date': date,
            'nombreActions': len(day_activities),
            'nombreSessions': len(sessions),
            'premierAction': timestamps[0].strftime('%H:%M'),
            'derniereAction': timestamps[-1].strftime('%H:%M'),
            'dureeEffective': round(total_duration, 2),
            'sessions': sessions
        })

    return work_analysis

def generate_dashboard_data(engagements):
    """Génère les données complètes du dashboard."""
    formatted_engagements = format_engagements(engagements)
    work_analysis = calculate_work_sessions(formatted_engagements)

    # Statistiques par type
    type_counts = defaultdict(int)
    for e in formatted_engagements:
        type_counts[e['type']] += 1

    stats = {
        'total': len(formatted_engagements),
        'emails': type_counts.get('EMAIL', 0),
        'calls': type_counts.get('CALL', 0),
        'tasks': type_counts.get('TASK', 0),
        'notes': type_counts.get('NOTE', 0),
        'meetings': type_counts.get('MEETING', 0),
        'by_type': dict(type_counts)  # Tous les types
    }

    # Dates
    if formatted_engagements:
        dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in formatted_engagements]
        stats['period_start'] = min(dates).strftime('%d/%m/%Y')
        stats['period_end'] = max(dates).strftime('%d/%m/%Y')
        stats['days'] = (max(dates) - min(dates)).days + 1

    # Activité par jour
    daily_activity = []
    by_date = defaultdict(lambda: {'emails': 0, 'calls': 0, 'total': 0})
    for eng in formatted_engagements:
        date = eng['date']
        by_date[date]['total'] += 1
        if eng['type'] == 'EMAIL':
            by_date[date]['emails'] += 1
        elif eng['type'] == 'CALL':
            by_date[date]['calls'] += 1

    for date in sorted(by_date.keys()):
        dt = datetime.strptime(date, '%Y-%m-%d')
        daily_activity.append({
            'date': date,
            'label': dt.strftime('%d/%m'),
            'weekday': dt.strftime('%A'),
            'total': by_date[date]['total'],
            'emails': by_date[date]['emails'],
            'calls': by_date[date]['calls']
        })

    # Stats de travail
    total_work = sum(w['dureeEffective'] for w in work_analysis)
    stats['work'] = {
        'totalDuree': round(total_work, 2),
        'totalActions': stats['total'],
        'joursActifs': len(work_analysis),
        'moyDuree': round(total_work / len(work_analysis), 2) if work_analysis else 0,
        'moyActions': stats['total'] // len(work_analysis) if work_analysis else 0
    }

    # Top contacts
    contacts_count = defaultdict(int)
    for eng in formatted_engagements:
        if eng['type'] == 'EMAIL' and 'to' in eng:
            for contact in eng['to']:
                if isinstance(contact, dict):
                    email = contact.get('email', '')
                    if email:
                        contacts_count[email] += 1

    top_contacts = []
    for email, count in sorted(contacts_count.items(), key=lambda x: x[1], reverse=True)[:20]:
        # Extraire le nom de l'email
        name_parts = email.split('@')[0].split('.')
        top_contacts.append({
            'firstName': name_parts[0].capitalize() if name_parts else '',
            'lastName': name_parts[1].capitalize() if len(name_parts) > 1 else '',
            'email': email,
            'count': count
        })

    # Calcul des stats d'appels détaillées
    disposition_map = {
        '9d9162e7-6cf3-4944-bf63-4dff82258764': 'Pas de réponse',
        '73a0d17f-1163-4015-bdd5-ec830791da20': 'Connecté',
        '62bfe711-0e16-4909-933d-9373418d63d7': 'Occupé',
        'f240bbac-87c9-4f6e-bf70-924b57d47db7': 'Message laissé',
        '17b47fee-58de-441e-a44c-c6300d46f273': 'Mauvais numéro',
        'a4c4c377-d246-4b32-a13b-75a56a4cd0ff': 'Autre',
        'b2cf5968-551e-4856-9783-52b3da59a7d0': 'Message à une personne'
    }

    call_details = {
        'total': 0,
        'connected': 0,
        'not_connected': 0,
        'by_disposition': {},
        'total_duration_connected': 0,
        'avg_duration_connected': 0
    }

    for eng in formatted_engagements:
        if eng['type'] == 'CALL':
            call_details['total'] += 1
            disp_id = eng.get('disposition')
            if disp_id:
                label = disposition_map.get(disp_id, 'Non catégorisé')
                call_details['by_disposition'][label] = call_details['by_disposition'].get(label, 0) + 1

                if disp_id == '73a0d17f-1163-4015-bdd5-ec830791da20':  # Connecté
                    call_details['connected'] += 1
                    if eng.get('duration'):
                        call_details['total_duration_connected'] += eng['duration']
                else:
                    call_details['not_connected'] += 1

    # Calculer durée moyenne
    if call_details['connected'] > 0:
        call_details['avg_duration_connected'] = round(
            (call_details['total_duration_connected'] / 1000 / 60) / call_details['connected'], 1
        )
    call_details['total_duration_connected'] = round(
        call_details['total_duration_connected'] / 1000 / 60, 1
    )

    stats['call_details'] = call_details

    # Calcul des objectifs et salaire
    jours_actifs = stats['work']['joursActifs']
    objectifs_config = {
        'calls_per_day': 30,
        'emails_per_day': 30,
        'salary_per_day': 200
    }

    objectif_calls = objectifs_config['calls_per_day'] * jours_actifs
    objectif_emails = objectifs_config['emails_per_day'] * jours_actifs
    objectif_total = objectif_calls + objectif_emails

    realise_calls = stats['calls']
    realise_emails = stats['emails']
    realise_total = realise_calls + realise_emails

    taux_calls = round((realise_calls / objectif_calls) * 100, 1) if objectif_calls > 0 else 0
    taux_emails = round((realise_emails / objectif_emails) * 100, 1) if objectif_emails > 0 else 0
    taux_global = round((realise_total / objectif_total) * 100, 1) if objectif_total > 0 else 0

    salaire_base = objectifs_config['salary_per_day'] * jours_actifs
    salaire_proratise = round(salaire_base * (taux_global / 100))

    stats['objectifs'] = {
        'config': objectifs_config,
        'jours_actifs': jours_actifs,
        'objectif_calls': objectif_calls,
        'objectif_emails': objectif_emails,
        'objectif_total': objectif_total,
        'realise_calls': realise_calls,
        'realise_emails': realise_emails,
        'realise_total': realise_total,
        'taux_calls': taux_calls,
        'taux_emails': taux_emails,
        'taux_global': taux_global,
        'salaire_base': salaire_base,
        'salaire_proratise': salaire_proratise
    }

    return {
        'stats': stats,
        'engagements': formatted_engagements,
        'daily_activity': daily_activity,
        'work_analysis': work_analysis,
        'top_contacts': top_contacts,
        'session_gap_minutes': SESSION_GAP_MINUTES
    }

def main():
    """Point d'entrée principal."""
    print("🚀 Démarrage de la mise à jour du dashboard HubSpot")
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

    if not HUBSPOT_TOKEN:
        print("❌ Erreur: HUBSPOT_TOKEN non défini dans les variables d'environnement")
        exit(1)

    try:
        # Récupérer les données
        engagements = fetch_engagements()

        # Générer les données du dashboard
        print("\n📊 Génération des données du dashboard...")
        dashboard_data = generate_dashboard_data(engagements)

        # Sauvegarder les données
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Données sauvegardées: data.json")
        print(f"\n📈 Résumé:")
        print(f"  • Total activités: {dashboard_data['stats']['total']}")

        # Afficher tous les types d'engagements
        by_type = dashboard_data['stats'].get('by_type', {})
        for eng_type, count in sorted(by_type.items()):
            type_emoji = {
                'EMAIL': '📧',
                'CALL': '📞',
                'TASK': '✅',
                'NOTE': '📝',
                'MEETING': '🤝'
            }.get(eng_type, '📌')
            print(f"  • {type_emoji} {eng_type}: {count}")

        print(f"  • Temps de travail: {dashboard_data['stats']['work']['totalDuree']}h")
        print(f"  • Jours actifs: {dashboard_data['stats']['work']['joursActifs']}")
        print(f"\n✨ Mise à jour terminée avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
