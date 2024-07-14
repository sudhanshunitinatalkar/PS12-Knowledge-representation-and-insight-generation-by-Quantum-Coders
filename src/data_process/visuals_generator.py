import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np
# for using Agg backend
import matplotlib
matplotlib.use('Agg')

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_plot(image, plot_type, x_axis=None, y_axis=None):
    # Get the path to the 'processed' folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(current_dir, '..', 'visuals_processed', 'visual_images')
    
    # Ensure the 'visual_images' directory exists in the 'processed' folder
    ensure_directory_exists(processed_dir)
    
    '''Create a subfolder for the plot type
    plot_type_dir = os.path.join(processed_dir, plot_type)
    ensure_directory_exists(plot_type_dir)''' 
    
    if plot_type in ['correlation_matrix', 'pie_chart']:
        filename = f"{plot_type}_{x_axis}.png" if x_axis else f"{plot_type}.png"
    else:
        filename = f"{plot_type}_{x_axis}_{y_axis}.png"
        
    filepath = os.path.join(processed_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(image.split(',')[1]))
    
    print(f"Plot saved: {filepath}")
    

# generates heatmap for correlation matrix
def generate_correlation_matrix(df):
    img = io.BytesIO()
    plt.figure(figsize=(20, 10))
    
    numeric_df = df.select_dtypes(include=['number'])
    cmap = sns.light_palette("seagreen", as_cmap=True)
    heatmap = sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", cmap=cmap)
    heatmap.set_xticklabels(heatmap.get_xticklabels(), fontsize=12, rotation=45, ha='right')
    heatmap.set_yticklabels(heatmap.get_yticklabels(), fontsize=12)
    plt.title('Correlation Matrix', fontsize=25, pad=20)
    plt.tight_layout()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# generates pie chart
def generate_pie_chart(df, x_axis):
    colors = None
    img = io.BytesIO()
    plt.figure(figsize=(7, 5))
    df[x_axis] = df[x_axis].astype('category')
    value_counts = df[x_axis].value_counts()
    total_count = value_counts.sum()
    percentages = value_counts / total_count
    other_mask = percentages < 0.02
    if other_mask.any():
        other_count = value_counts[other_mask].sum()
        value_counts = value_counts[~other_mask]
        value_counts['Other'] = other_count
    percentages = value_counts / value_counts.sum()
    show_numbers = not all(abs(p - percentages.mean()) < 0.05 for p in percentages)
    if colors:
        wedges, texts, autotexts = plt.pie(value_counts, 
                                           labels=value_counts.index if not show_numbers else None,
                                           autopct='%1.1f%%' if show_numbers else None, 
                                           startangle=90, 
                                           textprops=dict(color="w"), 
                                           pctdistance=0.85,
                                           wedgeprops=dict(width=0.4), 
                                           colors=colors[:len(value_counts)])
    else:
        wedges, texts, autotexts = plt.pie(value_counts, 
                                           labels=value_counts.index if not show_numbers else None,
                                           autopct='%1.1f%%' if show_numbers else None, 
                                           startangle=90, 
                                           textprops=dict(color="w"), 
                                           pctdistance=0.85,
                                           wedgeprops=dict(width=0.4))
    plt.tight_layout()
    plt.axis('equal')
    if show_numbers:
        plt.legend(value_counts.index, title=x_axis, loc="center", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.title(f'{x_axis.capitalize()} Count Piechart', fontsize=30)
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# processes x-axis for box plot
def process_x_axis(df, x_axis, max_categories=15):
    value_counts = df[x_axis].value_counts()
    if len(value_counts) > max_categories:
        top_categories = value_counts.nlargest(max_categories - 1)
        other_count = value_counts.sum() - top_categories.sum()
        top_categories['Others'] = other_count
        df[x_axis] = df[x_axis].map(lambda x: x if x in top_categories.index else 'Others')
    return df

# generates box plot
def generate_box_plot(df, x_axis, y_axis):
    df = process_x_axis(df, x_axis)
    img = io.BytesIO()
    plt.figure(figsize=(17, 8))
    sns.set_style("whitegrid")
    num_categories = len(df[x_axis].unique())
    light_blue_palette = sns.light_palette("#ADD8E6", n_colors=num_categories, reverse=True)
    ax = sns.boxplot(data=df, x=x_axis, y=y_axis, hue=x_axis,
                     palette=light_blue_palette, showfliers=False,
                     medianprops={"color": "#4682B4"}, legend=False,
                     width=0.5)
    plt.xticks(rotation=90, ha='right', fontsize=10)
    plt.xlabel(x_axis, fontsize=14, labelpad=20)
    plt.ylabel(y_axis, fontsize=14, labelpad=20)
    plt.title(f'Box Plot of {y_axis} by {x_axis}', fontsize=18, pad=20)
    sns.despine()
    plt.tight_layout()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# generates line plot
def generate_line_plot(df, x_axis, y_axis):
    df = process_x_axis(df, x_axis)
    img = io.BytesIO()
    plt.figure(figsize=(14, 7))
    sns.set_style("whitegrid")
    if df[x_axis].dtype == 'datetime64[ns]':
        df = df.sort_values(x_axis)
    elif df[x_axis].dtype == 'object':
        try:
            df[x_axis] = pd.to_datetime(df[x_axis])
            df = df.sort_values(x_axis)
        except:
            df = df.sort_values(x_axis)
    sns.lineplot(data=df, x=x_axis, y=y_axis, marker='o')
    plt.xticks(rotation=90, ha='right', fontsize=10)
    plt.xlabel(x_axis, fontsize=14, labelpad=10)
    plt.ylabel(y_axis, fontsize=14, labelpad=10)
    plt.title(f'Line Plot of {y_axis} over {x_axis}', fontsize=18, pad=20)
    sns.despine()
    plt.tight_layout()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# generates histogram
def generate_histogram(df, x_axis, y_axis):
    df = process_x_axis(df, x_axis)
    img = io.BytesIO()
    plt.figure(figsize=(22, 15))
    if df[x_axis].dtype == object or df[x_axis].dtype.name == 'category':
        categories = df[x_axis].astype('category').cat.categories
        bin_means = [df[df[x_axis] == category][y_axis].mean() for category in categories]
        plt.bar(categories, bin_means, color='skyblue', edgecolor='black')
        plt.xticks(rotation=45, fontsize=14)
    else:
        bins = np.linspace(df[x_axis].min(), df[x_axis].max(), 31)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        bin_means = np.zeros(len(bin_centers))
        for i in range(len(bins) - 1):
            mask = (df[x_axis] >= bins[i]) & (df[x_axis] < bins[i+1])
            if mask.sum() > 0:
                bin_means[i] = df.loc[mask, y_axis].mean()
        plt.bar(bin_centers, bin_means, width=(bins[1] - bins[0]), color='skyblue', edgecolor='black')
        plt.xticks(fontsize=14)
    plt.title(f'Histogram of {x_axis} showing average {y_axis}', fontsize=20)
    plt.xlabel(x_axis, fontsize=16)
    plt.ylabel(f'Average {y_axis}', fontsize=16)
    plt.yticks(fontsize=14)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# generates scatter plot
def generate_scatterplot(df, x_axis, y_axis):
    # Check if columns exist
    if x_axis not in df.columns or y_axis not in df.columns:
        raise ValueError(f"Columns {x_axis} and/or {y_axis} not found in DataFrame.")
    
    # Check if columns are numeric
    if not pd.api.types.is_numeric_dtype(df[x_axis]) or not pd.api.types.is_numeric_dtype(df[y_axis]):
        raise ValueError("Both x_axis and y_axis must be numerical columns.")
    
    img = io.BytesIO()
    plt.figure(figsize=(22, 10))
    sns.scatterplot(data=df, x=x_axis, y=y_axis, s=10, alpha=0.5)  # smaller points and alpha blending
    plt.title(f'Scatterplot of {x_axis} vs {y_axis}', fontsize=20)
    plt.xlabel(x_axis, fontsize=16)
    plt.ylabel(y_axis, fontsize=16)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

# generates plot
def generate_plot(df, plot_type, x_axis=None, y_axis=None):
    if plot_type == 'correlation_matrix':
        image = generate_correlation_matrix(df)
    elif plot_type == 'pie_chart':
        image = generate_pie_chart(df, x_axis)
    elif plot_type == 'box_plot':
        image = generate_box_plot(df, x_axis, y_axis)
    elif plot_type == 'line_plot':
        image = generate_line_plot(df, x_axis, y_axis)
    elif plot_type == 'histogram':
        image = generate_histogram(df, x_axis, y_axis)
    elif plot_type == 'scatterplot':
        image = generate_scatterplot(df, x_axis, y_axis)
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    
    save_plot(image, plot_type, x_axis, y_axis)
