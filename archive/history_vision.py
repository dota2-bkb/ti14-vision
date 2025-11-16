import cv2
import argparse
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import timedelta


def to_timedelta(t):
    parts = list(map(int, t.split(":")))
    if len(parts) == 2:  # mm:ss
        minutes, seconds = parts
        return timedelta(minutes=minutes, seconds=seconds)
    elif len(parts) == 3:  # hh:mm:ss
        hours, minutes, seconds = parts
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    else:
        raise ValueError("Unsupported time format")


def parse_events(file_path, map_width, map_height):


    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    events = []

    # Assuming events are in a specific HTML structure, e.g., <div class="event">
    idx = 0
    soup = soup.find('div', class_='match-log')
    for event_div in soup.find_all('div', class_='event'):
        data_div = event_div.find('div', class_='line')
        if data_div is None:
            continue
        # print(data_div)
        # break

        event = {}
        event['time'] = data_div.find('span', class_='time').get_text(strip=True) if data_div.find('span', class_='time') else None
        if event['time'] is None:
            continue

        action = data_div.find('div', class_='event').get_text()
        # remove extra \n and spaces in action
        action = ' '.join(action.split())
        event['action'] = action
        event['key_action'] = None
        if 'placed' in action and 'Observer Ward' in action:
            event['key_action'] = 'placed'
        elif 'activated' in action:
            event['key_action'] = 'smoke'
        elif 'destroyed' in action and 'Observer Ward' in action:
            event['key_action'] = 'destroyed'
        else:
            continue

        if event['key_action'] != None:
            pos_span = data_div.find('span', class_='minimap-tooltip')
            who_span = data_div.find('a', class_='color-faction-radiant')
            if who_span:
                event['side'] = 'Radiant'
            else:
                event['side'] = 'Dire'

            if pos_span:
                map_item = pos_span.find('span', class_='map-item')
                if map_item and 'style' in map_item.attrs:
                    style = map_item['style']
                    # Extract left and top percentages from style

                    event['hero'] = event['action'].split(' ')[0]
                    left_str = style.split('left:')[1].split('%')[0].strip()
                    top_str = style.split('top:')[1].split('%')[0].strip()
                    event['position'] = {
                        'left_percent': float(left_str),
                        'top_percent': float(top_str)
                    }
                    
                else:
                    continue
            else:
                continue

            # Do something with placed events
        events.append(event)
        # print('event idx:', idx, event_div)

        position = event['position']
    
        left = position['left_percent']
        top = position['top_percent']
        left = left * 0.01 * map_width
        top = top * 0.01 * map_height
        event['position_px'] = (int(left), int(top))
        
        # cv2.circle(dota_map, event['position_px'], 10, (0, 0, 255), -1)
        # event['position_px'] = (int(left)-10, int(top)-15)
        # cv2.putText(dota_map, event['time'], event['position_px'], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # cv2.imshow('dota_map', dota_map)
        # cv2.waitKey(0)
    
    # print(events)
    return events

if __name__ == "__main__":
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--team', type=str, default='falcon', choices=['falcon', 'pari'])
    args = argparse.parse_args()
    game_name = args.team
    assert game_name in ['falcon', 'pari']

    csv_path = f'game_{game_name}.csv'
    only_falcon_xg = False

    df = pd.read_csv(csv_path)
    game_num = len(df)
    print('total game num:', game_num)

    dota_map = cv2.imread('dota2_map.jpg')
    map_height, map_width, _ = dota_map.shape

    out_dir = Path(f'output_{game_name}_{"only_falcon_xg" if only_falcon_xg else "all"}')
    out_dir.mkdir(exist_ok=True)

    sides = ['Dire', 'Radiant']
    vis_time_slots = [0, 6, 12, 20, 40, 100]
    smoke_time_slots = [20]
    game_color = [
        (0, 0, 255),
        (0, 255, 0),
        (255, 0, 0),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (0, 128, 255),
        (128, 0, 255),
        (128, 128, 255),
        (128, 255, 0),
        (255, 128, 0),
        (255, 128, 128),
        (255, 0, 128),
        (128, 0, 128),
        (128, 128, 128),
        (128, 255, 255),
        (255, 128, 255),
        (255, 255, 128),
        (255, 255, 255),
    ]
    for side in sides:
        # if side != 'Radiant':
            # continue
        events_summary = []
        event_names = []
        for i in range(0, game_num):
            if game_name == 'falcon':
                str_name = 'Falcon 天辉/夜魇'
            elif game_name == 'pari':
                str_name = 'Pari 天辉/夜魇'
            else:
                raise ValueError(f'Invalid game name: {game_name}')
            game_side = df.iloc[i][str_name]
            if game_side != side:
                continue
            game_id = df.iloc[i]['比赛id']
            if only_falcon_xg and game_id not in [8447554972, 8447613945, 8447703577]:
                continue

            data_html_path = Path(f'data_{game_name}') / f'Match {game_id} - Vision - DOTABUFF - Dota 2 Stats.html'
            events = parse_events(data_html_path, map_width, map_height)
            events_summary.append(events)
            event_names.append(df.iloc[i]['场次'])
            # convert events to csv
            events_df = pd.DataFrame(events)
            events_df.to_csv(out_dir / f'{side}_{game_id}.csv', index=False)
            print(f'{side}_{game_id}.csv saved')

        if True:
            for time_idx, vis_time_slot in enumerate(vis_time_slots):

                print(f'time_idx: {time_idx}, vis_time_slot: {vis_time_slot}')
                vis_map = dota_map.copy()
                for game_idx, game_event in enumerate(events_summary):
                    if game_idx >= len(game_color):
                        break

                    for event in game_event:
                        if event['key_action'] != 'placed':
                            continue
                        if time_idx == 0:
                            if event['time'][0] != '-':
                                continue
                        else:
                            
                            if event['time'][0] == '-':
                                continue
                            prev_time = to_timedelta(f'{vis_time_slots[time_idx - 1]}:00')
                            cur_time = to_timedelta(f'{vis_time_slots[time_idx]}:00')
                            event_time = to_timedelta(f'{event["time"]}')
                            if event_time < prev_time or event_time >= cur_time:
                                continue
                        
                        if event['side'] != side:
                            continue

                        cv2.circle(vis_map, event['position_px'], 10, game_color[game_idx], -1)
                        text_pos = (int(event['position_px'][0])-10, int(event['position_px'][1])-15)
                        cv2.putText(vis_map, event['time'] + f'({event["hero"]})', text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)
                        
                    # add the game name, game color to the map
                    cv2.putText(vis_map, f'{event_names[game_idx]}', (vis_map.shape[1] - 300, game_idx * 30 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, game_color[game_idx], 2)

                if game_name == 'falcon':
                    title = 'Falcon'
                elif game_name == 'pari':
                    title = 'Pari'
                
                if side == 'Radiant':
                    title += ' Radiant'
                else:
                    title += ' Dire'
                if vis_time_slot == 0:
                    title += ' <0 min'
                elif vis_time_slot == 6:
                    title += ' 0-6 min'
                elif vis_time_slot == 12:
                    title += ' 6-12 min'
                elif vis_time_slot == 20:
                    title += ' 12-20 min'
                elif vis_time_slot == 40:
                    title += ' 20-40 min'
                elif vis_time_slot == 100:
                    title += ' 40-100 min'
                cv2.putText(vis_map, f'{title}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2)
                cv2.putText(vis_map, 'Made by SPACE', (50, vis_map.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2)
                cv2.imwrite(str(out_dir / f'{side}_before_{vis_time_slot}_minutes.jpg'), vis_map)
                print(f'{side}_{vis_time_slot}.jpg saved')
                
                
        if True:
            for time_idx in range(3):

                print(f'time_idx: {time_idx}')
                vis_map = dota_map.copy()
                for game_idx, game_event in enumerate(events_summary):
                    if game_idx >= len(game_color):
                        break

                    last_smoke_time = None
                    for event in game_event:
                        if event['key_action'] != 'smoke':
                            continue
                        
                        if event["time"][0] == '-':
                            continue

                        pd_time = to_timedelta('20:00')
                        pd2_time = to_timedelta('40:00')
                        event_time = to_timedelta(f'{event["time"]}')
                        if last_smoke_time is not None and event_time - last_smoke_time < to_timedelta('01:00'):
                            continue

                        if time_idx == 0 and (event_time >= pd_time):
                            continue
                        elif time_idx == 1 and (event_time < pd_time or event_time >= pd2_time):
                            continue
                        elif time_idx == 2 and (event_time < pd2_time):
                            continue

                        if event['side'] != side:
                            continue

                        last_smoke_time = event_time

                        cv2.circle(vis_map, event['position_px'], 10, game_color[game_idx], -1)
                        text_pos = (int(event['position_px'][0])-10, int(event['position_px'][1])-15)
                        cv2.putText(vis_map, event['time'] + f'({event["hero"]})', text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)
                        
                    # add the game name, game color to the map
                    cv2.putText(vis_map, f'{event_names[game_idx]}', (vis_map.shape[1] - 300, game_idx * 30 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, game_color[game_idx], 2)

                if game_name == 'falcon':
                    title = 'Falcon'
                elif game_name == 'pari':
                    title = 'Pari'
                else:
                    raise ValueError(f'Invalid game name: {game_name}')

                if side == 'Radiant':
                    title += 'Smoke-Radiant'
                else:
                    title += 'Smoke-Dire'
                if time_idx == 0:
                    title += ' <20 min'
                elif time_idx == 1:
                    title += ' 20-40 min'
                elif time_idx == 2:
                    title += ' 40-end min'

                cv2.putText(vis_map, f'{title}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 200), 2)
                cv2.putText(vis_map, 'Made by SPACE', (50, vis_map.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2)
                cv2.imwrite(str(out_dir / f'{title}.jpg'), vis_map)
                print(f'{title}.jpg saved')
                