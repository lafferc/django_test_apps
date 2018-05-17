import re
import csv
import datetime

g_summary_re = "(\w+) [vV]s? (\w+) .*"

def parse_events(file_name, debug=False):
    with open(file_name) as file:
        events = []
        event = None
        for line in file.readlines():
            line = line.strip()
            if not len(line):
               continue
            if debug:
                print(line)
            if "BEGIN:VEVENT" in line:
               event = {}
            elif event is None:
              continue
            elif "END:VEVENT" in line:
                if "SUMMARY" in event:
                    events.append(event)
                event = None
            else:
              try:
                  key, value = line.split(':')
                  event[key] = value
              except ValueError:
                  continue
        return events
    

def events_to_csv(events, file_name):
    header = ["match_id", "home_team", "away_team", "kick_off"]
    rows = []
    curr_id = 1
    for event in events:
        s = re.search(g_summary_re, event["SUMMARY"])
        row = {
           'match_id': curr_id,
           'home_team': s.group(1),
           'away_team': s.group(2),
           'kick_off': datetime.datetime.strptime(event["DTSTART"], "%Y%m%dT%H%M%SZ")
        }
        rows.append(row)
        curr_id += 1
        
    if len(rows):
        with open(file_name, 'w+') as file:
            writer = csv.DictWriter(file, fieldnames=header, )
            writer.writeheader()
            
            for row in rows:
                writer.writerow(row)


def events_to_teams(events, file_name):
    header = ["name", "code"]
    teams = []
    for event in events:
        s = re.search(g_summary_re, event["SUMMARY"])
        if s is None:
            continue
        if s.group(1) not in teams:
            teams.append(s.group(1))
        if s.group(2) not in teams:
            teams.append(s.group(2))
    if len(teams):
        with open(file_name, 'w+') as file:
            writer = csv.DictWriter(file, fieldnames=header, )
            writer.writeheader()
            for team in teams:
                writer.writerow({"name": team})
        

if __name__ == "__main__" :
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("in_filename")
    parser.add_argument("out_filename")
    parser.add_argument("-v", "--debug",
                        default=False,
                        action="store_true")
    parser.add_argument("--teams",
                        default=False,
                        action="store_true")
    args = parser.parse_args()
  
    events = parse_events(args.in_filename, args.debug)

    if args.teams:
        events_to_teams(events, args.out_filename)
    else:
        events_to_csv(events, args.out_filename)
