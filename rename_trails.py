import os

# Rename all trails named diff_* in the trails folder to trail_*
path = 'trails'
for filename in os.listdir(path):
    if filename.startswith('trail_'):
        
        # rescale difficulty
        diff = filename.split('_')[1].split('.')[0]
        new_diff = str(int(diff) +2)
        new_filename = filename.replace(f'trail_{diff}', f'trail_{new_diff}')
        print(f'Renaming {filename} to {new_filename}')

