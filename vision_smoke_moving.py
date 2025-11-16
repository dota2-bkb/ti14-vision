import cv2
import argparse
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from utils_vis import draw_arrow_fixed_tip


def to_timedelta(t):

    delta_time = 0
    if t[0] == '-':
        negative = True
        t = t[1:]
    else:
        negative = False

    parts = list(map(int, t.split(":")))
    if len(parts) == 2:  # mm:ss
        minutes, seconds = parts
        delta_time = minutes * 60 + seconds
    elif len(parts) == 3:  # hh:mm:ss
        hours, minutes, seconds = parts
        delta_time = hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError("Unsupported time format")

    if negative:
        if delta_time >= 0:
            delta_time = -delta_time

    return delta_time


def parse_events(file_path, map_width, map_height, key_player):


    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    events = []

    # check if the game side is Radiant or Dire
    res = soup.find('a', string=key_player)
    if 'radiant' in str(res).lower():
        side = 'radiant'
    else:
        side = 'dire'
    # print(side)

    # Assuming events are in a specific HTML structure, e.g., <div class="event">
    soup = soup.find('div', class_='match-log')

    hero_events = dict()
    observer_ward_cnt = 0

    for event_div in soup.find_all('div', class_='event'):
        data_div = event_div.find('div', class_='line')
        if data_div is None:
            continue
        # print(data_div)
        # break

        heros = data_div.find_all('a', class_=f'color-faction-{side}')
        if len(heros) == 0:
            # not the action we are interested in
            continue

        event = {}
        event['time'] = data_div.find('span', class_='time').get_text(strip=True) if data_div.find('span', class_='time') else None

        action = data_div.find('div', class_='event').get_text()
        # remove extra \n and spaces in action
        action = ' '.join(action.split())

        event['action'] = action
        event['key_action'] = None
        if 'placed a Observer Ward' in action:
            event['key_action'] = 'placed_observer'
            observer_ward_cnt += 1
            event['observer_ward_cnt'] = observer_ward_cnt
        elif 'activated Smoke of Deceit to stealth' in action:
            event['key_action'] = 'smoke'
        elif 'placed a Sentry Ward' in action:
            event['key_action'] = 'placed_sentry'
        else:
            continue

        hero_names = set()
        for hero in heros:
            # hero_name is in <img> alt tag
            hero_name = hero.find('img')['alt']
            if hero_name not in hero_events:
                hero_events[hero_name] = []
            hero_names.add(hero_name)
            # print(hero_name)
        # print(action)

        pos_span = data_div.find('span', class_='minimap-tooltip')
        map_item = pos_span.find('span', class_='map-item')
    
        style = map_item['style']
        left_str = style.split('left:')[1].split('%')[0].strip()
        top_str = style.split('top:')[1].split('%')[0].strip()
        event['position'] = {
            'left_percent': float(left_str),
            'top_percent': float(top_str)
        }

        left = float(left_str) * 0.01 * map_width
        top = float(top_str) * 0.01 * map_height
        event['position_px'] = (int(left), int(top))
        # Extract left and top percentages from style

        for hero_name in list(hero_names):
            hero_events[hero_name].append(event)
    # print(hero_events)
   
    return hero_events, side


if __name__ == "__main__":
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--team', type=str, default='yb', choices=['yb'])
    argparse.add_argument('--ward-cnt', type=int, default=2)
    argparse.add_argument('--top-n', type=int, default=None)
    args = argparse.parse_args()
    team_name = args.team
    assert team_name in ['yb']

    max_ward_cnt = args.ward_cnt
    print('Collecting events with observer ward count <=', max_ward_cnt)

    games = list(Path(f'data_{team_name}').glob('*.html'))
    games = sorted(games, key=lambda x: int(x.stem.split(' ')[1]), reverse=True)
    game_num = len(games)
    print('total game num:', game_num)

    dota_map = cv2.imread('dota2_map.jpg')
    map_height, map_width, _ = dota_map.shape

    out_dir = Path(f'output_{team_name}')
    out_dir.mkdir(exist_ok=True)

    sides = ['dire', 'radiant']
    game_color = [
        (0, 0, 255),
        (0, 255, 0),
        # (255, 0, 0),
        (255, 255, 0),
        (255, 0, 255),
        # (0, 255, 255),
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
    # smoke color is purple
    smoke_color = (173, 13, 106)
    # observer ward color is yellow
    observer_ward_color = (0, 255, 255)
    sentry_ward_color = (255, 0, 0)
    key_players = {
        'yb': 'YB.BoBoKa',
    }
    
    events_summary = []

    for i in tqdm(range(0, game_num), desc='Processing games'):
        data_html_path = games[i]
        events, side = parse_events(data_html_path, map_width, map_height, key_player=key_players[team_name])
        events_summary.append({
            'events': events,
            'side': side,
            'game_id': data_html_path.stem.split(' ')[1],
        })
    
    for side in sides:
        print(f'Processing side: {side}')

        vis_map = dota_map.copy()
        game_idx = 0

        if side == 'dire':
            offset = 40
        else:
            offset = -25

        for _, game_event in enumerate(events_summary):

            game_side = game_event['side']
            if game_side != side:
                continue
            game_id = game_event['game_id']
            all_hero_events = game_event['events']
            key_heros = []
            cut_event_time = None

            for hero_name, hero_events in all_hero_events.items():

                key_hero = False
                for event in hero_events:
                    if event['key_action'] == 'placed_observer' and event['observer_ward_cnt'] <= max_ward_cnt:
                        key_hero = True
                        if event['observer_ward_cnt'] == max_ward_cnt:
                            cut_event_time = to_timedelta(event['time'])
                        # break
                    # elif event['key_action'] == 'placed_sentry':
                        # key_hero = True
                
                if key_hero:
                    key_heros.append(hero_name)

            # cut_event_time = 0
               
            for hero_name, hero_events in all_hero_events.items():

                if hero_name not in key_heros:
                    continue

                last_position_px = None
                for event in hero_events:
                    event_time = to_timedelta(f'{event["time"]}')
                    # print(event['time'])
                    if event_time > cut_event_time:
                        break

                    if event['key_action'] == 'smoke':

                        cv2.circle(vis_map, event['position_px'], 10, smoke_color, -1)
                        text_pos = (int(event['position_px'][0])-50, int(event['position_px'][1])+offset)
                        cv2.putText(vis_map, event['time'], text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)

                        if last_position_px is not None:
                            draw_arrow_fixed_tip(vis_map, last_position_px, event['position_px'], game_color[game_idx], 2)
                        last_position_px = event['position_px']
                    elif event['key_action'] == 'placed_observer':
                        cv2.circle(vis_map, event['position_px'], 10, observer_ward_color, -1)
                        text_pos = (int(event['position_px'][0])-50, int(event['position_px'][1])+offset)
                        cv2.putText(vis_map, event['time'] + f"[{str(event['observer_ward_cnt'])}]", text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)
                        if last_position_px is not None:
                            draw_arrow_fixed_tip(vis_map, last_position_px, event['position_px'], game_color[game_idx], 2)
                        last_position_px = event['position_px']

                    elif event['key_action'] == 'placed_sentry':
                        cv2.circle(vis_map, event['position_px'], 10, sentry_ward_color, -1)
                        text_pos = (int(event['position_px'][0])-50, int(event['position_px'][1])+offset)
                        cv2.putText(vis_map, event['time'], text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)
                        if last_position_px is not None:
                            draw_arrow_fixed_tip(vis_map, last_position_px, event['position_px'], game_color[game_idx], 2)
                        last_position_px = event['position_px']

            # set gray background for the game id
            cv2.rectangle(vis_map, (vis_map.shape[1] - 260, game_idx * 40+20), (vis_map.shape[1]-40, game_idx * 40 + 70), (128, 128, 128), -1)
            cv2.putText(vis_map, f'{game_id}', (vis_map.shape[1] - 250, game_idx * 40 + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[game_idx], 2)
            
            game_idx += 1
            if args.top_n is not None and game_idx >= args.top_n:
                break
                   
        title = f'{team_name}-{side}-Wards<={max_ward_cnt}'
        if args.top_n is not None:
            title += f'-Top {args.top_n} Games'
       
        cv2.putText(vis_map, f'{title}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200), 2)
        cv2.putText(vis_map, 'Made by SPACE', (vis_map.shape[1] - 300, vis_map.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)
        cv2.imwrite(str(out_dir / f'{title}.jpg'), vis_map)
        print(f'{title}.jpg saved')

        # break
        