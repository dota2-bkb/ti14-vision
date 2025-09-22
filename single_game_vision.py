import argparse
from history_vision import parse_events, to_timedelta
from pathlib import Path
import cv2
import pandas as pd


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--team', type=str, default='falcon', choices=['falcon', 'pari'])
    parser.add_argument('--game_id', type=int, default=8461854486, choices=[8461735141, 8461613337, 8461476910])
    parser.add_argument('--our_side', type=str, default='Dire', choices=['Dire', 'Radiant'])
    parser.add_argument('--enemy_team', type=str, default='falcon', choices=['falcon', 'pari'])
    args = parser.parse_args()
    game_name = args.team
    assert game_name in ['falcon', 'pari']
    game_id = args.game_id
    our_side = args.our_side
    if our_side == 'Dire':
        enemy_side = 'Radiant'
    else:
        enemy_side = 'Dire'
    enemy_team = args.enemy_team
    assert enemy_team in ['falcon', 'pari']

    out_dir = Path(f'output_{enemy_team}')
    out_dir.mkdir(exist_ok=True)

    data_html_path = Path(f'data_{enemy_team}') / f'Match {game_id} - Vision - DOTABUFF - Dota 2 Stats.html'

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
    vis_time_slots = [0, 6, 12, 20, 40, 100]


    hero_dict = {
        'Enchantress': 'xiaolu',
        'Snapfire': 'laonainai',
        'Seven': 'Siwen',
        'Ember': 'huomao',
        'Pangolier': 'cike',
    }

    dota_map = cv2.imread('dota2_map.jpg')
    map_height, map_width, _ = dota_map.shape

    events = parse_events(data_html_path, map_width, map_height)
    events_df = pd.DataFrame(events)
    events_df.to_csv(out_dir / f'{enemy_side}_{game_id}.csv', index=False)
    print(f'{enemy_side}_{game_id}.csv saved')

    for time_idx, vis_time_slot in enumerate(vis_time_slots):

        print(f'time_idx: {time_idx}, vis_time_slot: {vis_time_slot}')
        vis_map = dota_map.copy()

        for eid, event in enumerate(events):
            if event['side'] == enemy_side:
                
                if event['key_action'] == 'placed':
                    
                
                    if event['time'][0] == '-':
                        event_time = to_timedelta('00:00')
                    else:
                        event_time = to_timedelta(f'{event["time"]}')

                    print(event['action'], event['hero'])
                    cv2.circle(vis_map, event['position_px'], 10, game_color[0], -1)
                    text_pos = (int(event['position_px'][0])-10, int(event['position_px'][1])-15)
                    cv2.putText(vis_map, event['time'], text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[0], 2)
                elif event['key_action'] == 'smoke':
                    cv2.circle(vis_map, event['position_px'], 10, game_color[2], -1)
                    text_pos = (int(event['position_px'][0])-10, int(event['position_px'][1])-15)
                    cv2.putText(vis_map, event['time'], text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[2], 2)
            elif event['side'] == our_side:
                if event['key_action'] != 'destroyed':
                    continue
                if event['time'][0] == '-':
                    continue
                
                cv2.circle(vis_map, event['position_px'], 10, game_color[1], -1)
                # text_pos = (int(event['position_px'][0])-10, int(event['position_px'][1])-15)
                # cv2.putText(vis_map, event['time'] + f'({hero_dict[event["hero"]]})', text_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, game_color[0], 2)
            # add the game name, game color to the map
            # cv2.putText(vis_map, f'{enemy_team} - {enemy_side}', (vis_map.shape[1] - 300, eid * 30 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, game_color[0], 2)

        title = f'{enemy_team}-{enemy_side}-{game_id}'
        
        cv2.putText(vis_map, f'{title}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2)
        cv2.putText(vis_map, 'Made by SPACE', (50, vis_map.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2)
        cv2.imwrite(str(out_dir / f'{title}.jpg'), vis_map)
        print(f'{title}.jpg saved')