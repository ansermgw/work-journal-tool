#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import logging
import sys

if __name__ == '__main__':
    if len(sys.argv) != 3:
        logging.error('Usage: main.py <source_path> <dest_path>')
        exit(1)

    source_path = sys.argv[1]
    dest_path = sys.argv[2]

    df = pd.read_csv(source_path, skipinitialspace=True)

    # convert dates
    for col in ['start', 'end']:
        df[col] = pd.to_datetime(df[col], format='%d.%m.%Y %H:%M')

    # convert categories
    df['category'] = df['category'].astype('category')
    df['category'].cat.categories.tolist()

    # check journal entry start is allways before end
    violations = df[df['start'] >= df['end']]
    if len(violations) > 0:
        logging.error('The following entries have a start time after the end time :\n')
        logging.error(violations)
        exit(1)


    # check journal does not contains overlapping entries
    # source: chatGPT
    df_sorted = df.sort_values(['start', 'end']).copy()

    prev_end = df_sorted['end'].shift()
    overlap_mask = df_sorted['start'] < prev_end
    overlaps = df_sorted[overlap_mask]
    if len(overlaps) > 0:
        logging.error('The following entries overlap with others :\n')
        logging.error(overlaps)
        exit(1)

    # feature engineering
    df['duration_hours'] = (df['end'] - df['start']).dt.total_seconds() / 3600
    df['start_week'] = df['start'].dt.to_period('W').dt.start_time

    weekly_df = df.groupby(["start_week", "category"])["duration_hours"].sum().reset_index()
    weekly_df_pivoted = weekly_df.pivot(index='start_week', columns='category', values='duration_hours').fillna(0).sort_index()

    fig, ax = plt.subplots(figsize=(15, 10))

    ax.stackplot(
            weekly_df_pivoted.index.to_pydatetime(),
            weekly_df_pivoted.T.values,
            labels=[str(c) for c in weekly_df_pivoted.columns],
        )

    ax.legend()
    ax.set_title(f"Weekly hours by category (total {df['duration_hours'].sum():.2f} h)")
    ax.set_xlabel("Week")
    ax.set_ylabel("Hours")

    fig.savefig(dest_path)