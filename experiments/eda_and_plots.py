import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

def run_eda_and_generate_plots():
    os.makedirs('docs/figures', exist_ok=True)
    os.makedirs('experiments/plots', exist_ok=True)

    df = pd.read_csv('data/train_cases.csv')
    df_test = pd.read_csv('data/test_cases.csv')
    df_all = pd.concat([df, df_test], ignore_index=True)

    print("=" * 60)
    print("EXPLORATORY DATA ANALYSIS (EDA) - SYNTHETIC INCIDENTS")
    print("=" * 60)
    print(f"Total Records: {len(df_all)}")
    print(f"Train Records: {len(df_all[df_all['split'] == 'train'])}")
    print(f"Test Records: {len(df_all[df_all['split'] == 'test'])}")
    print(f"Total Unique Clusters: {df_all['cluster_id'].nunique()}")
    print(f"Duplicate Ground Truth: {df_all['is_duplicate_ground_truth'].sum()} ({df_all['is_duplicate_ground_truth'].mean()*100:.1f}%)")
    print(f"Records with PII: {df_all['has_pii'].sum()} ({df_all['has_pii'].mean()*100:.1f}%)")
    
    print("\n--- Event Type Distribution (Table 1) ---")
    print(df_all['event_type'].value_counts(normalize=True).apply(lambda x: f"{x*100:.2f}%"))
    
    print("\n--- Latent Factor Distribution ---")
    print(df_all['latent_factor'].value_counts(normalize=True).apply(lambda x: f"{x*100:.2f}%"))

    # Plot 1: Class & Latent Factor Distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Event Types
    event_order = ['marginal_incident', 'near_miss', 'critical_incident']
    event_labels = ['Marginal Incident\n(Safety: Minor)', 'Near Miss\n(Safety: Near Miss)', 'Critical Incident\n(Safety: Accident)']
    event_colors = ['#3498db', '#e67e22', '#e74c3c']
    
    counts = [df_all['event_type'].value_counts().get(e, 0) for e in event_order]
    bars = axes[0].bar(event_labels, counts, color=event_colors, edgecolor='#2c3e50', alpha=0.85, width=0.55)
    axes[0].set_title('Event Type Distribution (Table 1 Swiss Cheese Taxonomy)', fontsize=12, fontweight='bold', pad=12)
    axes[0].set_ylabel('Number of Incidents', fontsize=11)
    for bar in bars:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 3, f'{yval} ({yval/len(df_all)*100:.1f}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')
    axes[0].set_ylim(0, max(counts) * 1.18)

    # Latent Factors
    latent_order = ['vulnerability', 'predisposing_condition']
    latent_labels = ['Vulnerability\n(Technical Weakness)', 'Predisposing Condition\n(Architecture/Culture)']
    latent_colors = ['#9b59b6', '#1abc9c']
    latent_counts = [df_all['latent_factor'].value_counts().get(l, 0) for l in latent_order]
    
    bars2 = axes[1].bar(latent_labels, latent_counts, color=latent_colors, edgecolor='#2c3e50', alpha=0.85, width=0.45)
    axes[1].set_title('Latent Factors Distribution (Reason Resident Pathogens)', fontsize=12, fontweight='bold', pad=12)
    axes[1].set_ylabel('Number of Incidents', fontsize=11)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 4, f'{yval} ({yval/len(df_all)*100:.1f}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')
    axes[1].set_ylim(0, max(latent_counts) * 1.18)

    plt.tight_layout()
    fig1_path = 'docs/figures/eda_class_and_latent_distribution.png'
    plt.savefig(fig1_path, dpi=300)
    plt.savefig('experiments/plots/eda_class_and_latent_distribution.png', dpi=300)
    plt.close()
    print(f"Saved figure 1: {fig1_path}")

    # Plot 2: Cluster Sizes & Duplicate Distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    cluster_sizes = df_all.groupby('cluster_id').size()
    
    sns.countplot(x=cluster_sizes, ax=axes[0], palette='Blues_r')
    axes[0].set_title('Distribution of Incident Cluster Sizes (Reports per Incident)', fontsize=12, fontweight='bold', pad=12)
    axes[0].set_xlabel('Number of Reports in Cluster', fontsize=11)
    axes[0].set_ylabel('Cluster Frequency', fontsize=11)
    for p in axes[0].patches:
        axes[0].annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='center', xytext=(0, 6), textcoords='offset points', fontweight='bold')

    # Threat Actor Pie Chart
    threat_counts = df_all['threat_actor'].value_counts()
    axes[1].pie(threat_counts.values, labels=threat_counts.index, autopct='%1.1f%%',
                colors=['#2ecc71', '#e74c3c', '#95a5a6'], startangle=140, explode=[0.03, 0.03, 0.03])
    axes[1].set_title('Threat Actor Distribution (Table 1)', fontsize=12, fontweight='bold', pad=12)

    plt.tight_layout()
    fig2_path = 'docs/figures/eda_cluster_and_actor_distribution.png'
    plt.savefig(fig2_path, dpi=300)
    plt.savefig('experiments/plots/eda_cluster_and_actor_distribution.png', dpi=300)
    plt.close()
    print(f"Saved figure 2: {fig2_path}")

    # Plot 3: Narrative Text Length Distribution
    df_all['word_count'] = df_all['narrative_text'].apply(lambda x: len(str(x).split()))
    
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df_all, x='event_type', y='word_count', palette=event_colors, order=event_order)
    plt.title('Narrative Word Count by Event Type', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Event Type (Table 1 Taxonomy)', fontsize=11)
    plt.ylabel('Word Count per Report', fontsize=11)
    plt.xticks([0, 1, 2], ['Marginal Incident', 'Near Miss', 'Critical Incident'])
    
    plt.tight_layout()
    fig3_path = 'docs/figures/eda_text_length_by_event.png'
    plt.savefig(fig3_path, dpi=300)
    plt.savefig('experiments/plots/eda_text_length_by_event.png', dpi=300)
    plt.close()
    print(f"Saved figure 3: {fig3_path}")
    print("EDA and Plot generation finished successfully!")

if __name__ == "__main__":
    run_eda_and_generate_plots()
