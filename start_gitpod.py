#!/usr/bin/env python3
import os
import sys
import argparse
import requests

API_ENDPOINT = 'https://api.gitpod.io/gitpod.v1.WorkspaceService/CreateAndStartWorkspace'

def main():
    parser = argparse.ArgumentParser(
        description='Starte eine Gitpod-Instanz über die Public API'
    )
    parser.add_argument(
        'context_url',
        help='Context URL für Gitpod, z.B. '
             '"https://gitpod.io/#MOODLE_REPOSITORY=https://github.com/sarjona/moodle.git,MOODLE_BRANCH=MDL-79912-main/https://github.com/moodlehq/moodle-docker"'
    )
    parser.add_argument(
        '--org-id',
        default=os.getenv('GITPOD_ORG_ID'),
        help='Gitpod Organization ID (env GITPOD_ORG_ID)'
    )
    parser.add_argument(
        '--owner-id',
        default=os.getenv('GITPOD_OWNER_ID'),
        help='Gitpod User/Owner ID (env GITPOD_OWNER_ID)'
    )
    parser.add_argument(
        '--workspace-class',
        default='g1-standard',
        help='Workspace-Ressourcenklasse (z.B. g1-standard)'
    )
    parser.add_argument(
        '--editor-name',
        default='code',
        help='Editor-Name (z.B. code, intellij, etc.)'
    )
    parser.add_argument(
        '--editor-version',
        default='latest',
        help='Editor-Version (z.B. stable, latest)'
    )

    args = parser.parse_args()

    token = os.getenv('GITPOD_TOKEN')
    if not token:
        sys.stderr.write('Error: Bitte setze die Umgebungsvariable GITPOD_TOKEN\n')
        sys.exit(1)
    if not args.org_id or not args.owner_id:
        sys.stderr.write(
            'Error: Bitte setze GITPOD_ORG_ID und GITPOD_OWNER_ID '
            'oder übergebe sie per --org-id/--owner-id\n'
        )
        sys.exit(1)

    payload = {
        "contextUrl": {
            "url": args.context_url,
            "workspaceClass": args.workspace_class,
            "editor": {
                "name": args.editor_name,
                "version": args.editor_version
            }
        },
        "metadata": {
            "ownerId": args.owner_id,
            "organizationId": args.org_id
        }
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    resp = requests.post(API_ENDPOINT, json=payload, headers=headers)
    if resp.status_code != 200:
        sys.stderr.write(
            f'Fehler beim Erstellen der Workspace (HTTP {resp.status_code}):\n'
            f'{resp.text}\n'
        )
        sys.exit(1)

    ws = resp.json().get('workspace', {})
    wid = ws.get('id')
    phase = ws.get('status', {}).get('phase')
    print('✅ Workspace gestartet:')
    print(f'   ID:     {wid}')
    print(f'   Status: {phase}')
    print(f'   URL:    https://gitpod.io/#workspace/{wid}')

if __name__ == '__main__':
    main() 