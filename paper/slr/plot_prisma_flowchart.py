"""
Generates publication-quality PRISMA 2020 Flowchart Figure (fig_prisma_flow.png)
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_prisma_flowchart():
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax.axis('off')

    # Color palette
    box_color = "#EBF3FB"
    edge_color = "#1B4F72"
    highlight_color = "#D4EFDF"
    highlight_edge = "#196F3D"

    # Box styles
    box_props = dict(boxstyle="round,pad=0.5", facecolor=box_color, edgecolor=edge_color, linewidth=1.5)
    excl_props = dict(boxstyle="round,pad=0.5", facecolor="#FDEDEC", edgecolor="#922B21", linewidth=1.2)
    incl_props = dict(boxstyle="round,pad=0.6", facecolor=highlight_color, edgecolor=highlight_edge, linewidth=2.0)

    # 1. Identification
    ax.text(0.30, 0.90, "IDENTIFICATION\nRecords identified from:\nOpenAlex (IEEE, ACM, ACL, arXiv): 5,979\nCrossref / arXiv Preprints: 2,145\n(Total: 8,124)", 
            ha="center", va="center", fontsize=9, bbox=box_props, fontweight="bold")
    
    ax.text(0.78, 0.90, "Duplicates removed\n(n = 1,842)", 
            ha="center", va="center", fontsize=9, bbox=excl_props)

    # Arrow to Screening
    ax.annotate('', xy=(0.30, 0.77), xytext=(0.30, 0.82), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))
    ax.annotate('', xy=(0.65, 0.90), xytext=(0.49, 0.90), arrowprops=dict(facecolor='black', shrink=0.05, width=1.2, headwidth=5))

    # 2. Screening
    ax.text(0.30, 0.70, "SCREENING\nRecords screened (Title & Abstract)\n(n = 6,282)", 
            ha="center", va="center", fontsize=9, bbox=box_props, fontweight="bold")

    ax.text(0.78, 0.70, "Records excluded (n = 5,984):\n• Not RAG / knowledge NLP: 3,842\n• Pure LLM/hardware: 1,420\n• Non-English / notes: 722", 
            ha="center", va="center", fontsize=8, bbox=excl_props)

    ax.annotate('', xy=(0.60, 0.70), xytext=(0.46, 0.70), arrowprops=dict(facecolor='black', shrink=0.05, width=1.2, headwidth=5))
    ax.annotate('', xy=(0.30, 0.57), xytext=(0.30, 0.63), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

    # 3. Retrieval
    ax.text(0.30, 0.50, "REPORTS SOUGHT\nReports sought for retrieval\n(n = 298)\nReports retrieved: 298", 
            ha="center", va="center", fontsize=9, bbox=box_props)

    ax.annotate('', xy=(0.30, 0.38), xytext=(0.30, 0.44), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

    # 4. Eligibility
    ax.text(0.30, 0.31, "ELIGIBILITY\nFull-text reports assessed\nfor eligibility\n(n = 298)", 
            ha="center", va="center", fontsize=9, bbox=box_props, fontweight="bold")

    ax.text(0.78, 0.31, "Full-text reports excluded (n = 256):\n• Monolithic prompt concatenation: 114\n• Lacking quantitative metrics: 82\n• Black-box commercial systems: 60", 
            ha="center", va="center", fontsize=8, bbox=excl_props)

    ax.annotate('', xy=(0.60, 0.31), xytext=(0.46, 0.31), arrowprops=dict(facecolor='black', shrink=0.05, width=1.2, headwidth=5))
    ax.annotate('', xy=(0.30, 0.18), xytext=(0.30, 0.24), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

    # 5. Included
    ax.text(0.30, 0.08, "INCLUDED\nFinal Studies Included in SLR (n = 42)\n• Epistemic Calibration & Uncertainty (n = 11)\n• Citation Attribution & Faithfulness (n = 12)\n• Contradiction Resolution & Dialectics (n = 9)\n• Multi-Hop Reasoning & Entailment Graphs (n = 10)", 
            ha="center", va="center", fontsize=9.5, bbox=incl_props, fontweight="bold")

    plt.title("PRISMA 2020 Systematic Literature Review Flow Diagram for Cogent", fontsize=12, fontweight="bold", pad=20)
    plt.tight_layout()

    out_path = os.path.join(os.path.dirname(__file__), "..", "figures", "fig_prisma_flow.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] PRISMA flowchart saved to: {out_path}")

if __name__ == "__main__":
    draw_prisma_flowchart()
