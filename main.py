"""PaceFlow Garmin direct POC. Unofficial Garmin Connect client; single account only."""
import argparse
import json
import os
from datetime import date
from getpass import getpass
from pathlib import Path


def workout_payload():
    def step(order, kind, end, value, target=None):
        s = {"type": "ExecutableStepDTO", "stepOrder": order,
             "stepType": {"stepTypeId": kind, "stepTypeKey": {1:"warmup",3:"interval",4:"recovery",2:"cooldown"}[kind]},
             "endCondition": {"conditionTypeId": 3 if end == 'distance' else 2, "conditionTypeKey": end},
             "endConditionValue": value}
        if target:
            s.update({"targetType": {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"},
                      "targetValueOne": target[0], "targetValueTwo": target[1]})
        return s
    # Garmin pace values are meters/second; 4:45/km = 3.50877, 4:30/km = 3.70370.
    steps = [step(1,1,'distance',2000)]
    for i in range(4):
        steps.append(step(len(steps)+1,3,'distance',2000,(1000/285,1000/270)))
        steps.append(step(len(steps)+1,4,'time',60))
    steps.append(step(len(steps)+1,2,'distance',2000))
    return {"workoutName":"PaceFlow Python POC - 4x2km", "sportType":{"sportTypeId":1,"sportTypeKey":"running"},
            "workoutSegments":[{"segmentOrder":1,"sportType":{"sportTypeId":1,"sportTypeKey":"running"},"workoutSteps":steps}]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--date',default='2026-10-09')
    p.add_argument('--send',action='store_true',help='Explicitly enable Garmin upload')
    p.add_argument('--push-device',action='store_true',help='Push to last used device after upload')
    args=p.parse_args()
    date.fromisoformat(args.date)
    payload=workout_payload()
    print('Séance: 2 km échauffement; 4 x (2 km à 4:30–4:45/km + 60 s récupération); 2 km retour au calme')
    print('Date:',args.date, '| étapes:',len(payload['workoutSegments'][0]['workoutSteps']))
    print(json.dumps(payload,indent=2,ensure_ascii=False))
    if not args.send:
        print('\nMODE APERÇU: aucune connexion ni modification Garmin. Utiliser --send après vérification.')
        return
    print('\nATTENTION: API GARMIN NON OFFICIELLE. Risque de blocage de compte / changement API.')
    if input('Tape ENVOYER pour confirmer la création et programmation : ').strip() != 'ENVOYER':
        print('Annulé.'); return
    from garminconnect import Garmin
    email=input('Adresse Garmin: ').strip()
    password=getpass('Mot de passe Garmin (non affiché): ')
    client=Garmin(email,password,prompt_mfa=lambda: input('Code MFA Garmin: ').strip())
    # No persistent token store; credentials stay only in the process.
    client.login()
    print('Connexion réussie. Envoi...')
    result=client.upload_workout(payload)
    workout_id=result.get('workoutId')
    if not workout_id:
        print('Réponse Garmin sans workoutId:',json.dumps(result,ensure_ascii=False));return
    print('Séance créée:',workout_id)
    scheduled=client.schedule_workout(workout_id,args.date)
    print('Programmation:',json.dumps(scheduled,ensure_ascii=False)[:500])
    if args.push_device:
        print('Envoi appareil:',str(client.push_workout_to_device(workout_id))[:500])
    print('Vérifie la séance et les allures dans Garmin Connect / montre.')

if __name__=='__main__':
    main()
