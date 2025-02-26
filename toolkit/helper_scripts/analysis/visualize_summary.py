import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from textwrap import wrap

TITLE_FONT_SIZE = 18
DARK_YELLOW = "#B8860B"
MAX_COMMIT_HISTORY = 60

def truncate_message(message, wrap_width, max_lines):
    """
    Wrap the message text to a given width and limit it to max_lines.
    If the message is longer than allowed, the last line is truncated with an ellipsis.
    """
    lines = wrap(message, wrap_width)
    if len(lines) > max_lines:
        # Take the first max_lines-1 full lines and then truncate the last line
        truncated_last_line = lines[max_lines - 1]
        if len(truncated_last_line) > wrap_width - 3:
            truncated_last_line = truncated_last_line[:wrap_width - 3] + '...'
        return "\n".join(lines[:max_lines - 1] + [truncated_last_line])
    else:
        return "\n".join(lines)

def load_json_files(folder_path):
    """Load and parse JSON files from the given folder."""
    data = []
    for file_name in sorted(os.listdir(folder_path)):  # Incremental version order
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = json.load(f)
                summary = content["summary"]
                summary["version"] = file_name.replace(".json", "")
                summary["core_refs"] = {f:l[1] for f, l in content["files"].items() if "LM_" not in f}
                data.append(summary)
    return data

def load_meta_files(folder_path):
    """Load and parse .meta files from the given folder."""
    meta_data = []
    for file_name in sorted(os.listdir(folder_path)):  # Incremental version order
        if file_name.endswith(".meta"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = f.read().strip()
                if ": " in content:
                    commit_id, commit_message = content.split(": ", 1)
                    version = file_name.replace(".meta", "")
                    meta_data.append({"version": version, "commit_id": commit_id, "message": commit_message})
    return meta_data

def load_release_versions(folder_path):
    release_versions = []
    try:
        with open(f"{folder_path}/release_versions.info", 'r') as f:
            release_versions = f.read().strip().split()
        release_versions = [v.replace("v", '').strip() for v in release_versions]
    except Exception as e:
        print("Error loading release_versions.info")
    return release_versions

def visualize_timeline(data, meta_data, highlighted_versions, output_pdf):
    """Generate timeline visualizations for all metrics and save to a PDF."""
    versions = [d["version"] for d in data]

    # Extract data for each timeline
    core_lines = [d["core"][0] for d in data]
    core_files = [d["core"][1] for d in data]
    load_lines = [d["load"][0] for d in data]
    load_files = [d["load"][1] for d in data]
    core_scores = [d["core_score"] for d in data]
    load_scores = [d["load_score"] for d in data]
    dependency_warnings = [d["load_dep"][1] for d in data]

    # Extract core_refs data per file
    all_files = sorted(set(f for d in data for f in d["core_refs"].keys()))
    core_refs_by_file = {f: [d["core_refs"].get(f, 0) for d in data] for f in all_files}

    with PdfPages(output_pdf) as pdf:
        # Use dark background style
        plt.style.use('dark_background')


        #########################################################
        # Plot 1: Core System – File Count (left) and Lines of Code (right)
        fig, ax_left = plt.subplots(figsize=(15, 8))
        # Left y-axis: File Count (teal)
        ax_left.plot(versions, core_files, label="File Count", color="teal", marker="x")
        ax_left.set_ylabel("File Count", color="teal")
        ax_left.tick_params(axis='y', labelcolor="teal")
        ax_left.set_xlabel("Versions")
        ax_left.set_xticks(range(len(versions)))
        ax_left.set_xticklabels(versions, rotation=90, fontsize=8)
        ax_left.grid(True, linestyle="--", alpha=0.1)

        # Highlight specific versions
        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax_left.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        # Annotate the last file count data point with fixed offset (10 pts to the right)
        ax_left.annotate(f'{core_files[-1]}',
                         xy=(len(versions)-1, core_files[-1]),
                         xytext=(10, 0), textcoords='offset points',
                         color="teal", fontsize=9,
                         arrowprops=dict(arrowstyle="->", color="teal"))

        # Right y-axis: Lines of Code (purple)
        ax_right = ax_left.twinx()
        ax_right.plot(versions, core_lines, label="Lines of Code", color="purple", marker="o")
        ax_right.set_ylabel("Lines of Code", color="purple")
        ax_right.tick_params(axis='y', labelcolor="purple")

        # Annotate the last line count data point with fixed offset (10 pts to the right)
        ax_right.annotate(f'{core_lines[-1]}',
                          xy=(len(versions)-1, core_lines[-1]),
                          xytext=(10, 0), textcoords='offset points',
                          color="purple", fontsize=9,
                          arrowprops=dict(arrowstyle="->", color="purple"))

        ax_left.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
        ax_right.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

        plt.title("Core System Evolution: File Count & Lines of Code", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 2: Load Modules – File Count (left) and Lines of Code (right)
        fig, ax_left = plt.subplots(figsize=(15, 8))
        # Left y-axis: File Count (teal)
        ax_left.plot(versions, load_files, label="File Count", color="teal", marker="x")
        ax_left.set_ylabel("File Count", color="teal")
        ax_left.tick_params(axis='y', labelcolor="teal")
        ax_left.set_xlabel("Versions")
        ax_left.set_xticks(range(len(versions)))
        ax_left.set_xticklabels(versions, rotation=90, fontsize=8)
        ax_left.grid(True, linestyle="--", alpha=0.1)

        # Highlight specific versions
        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax_left.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        # Adjust annotation offsets so labels don't overlap:
        # For the file count (left axis), move upward; for lines (right axis), move downward.
        ax_left.annotate(f'{load_files[-1]}',
                         xy=(len(versions)-1, load_files[-1]),
                         xytext=(10, 10), textcoords='offset points',
                         color="teal", fontsize=9,
                         arrowprops=dict(arrowstyle="->", color="teal"))

        # Right y-axis: Lines of Code (purple)
        ax_right = ax_left.twinx()
        ax_right.plot(versions, load_lines, label="Lines of Code", color="purple", marker="o")
        ax_right.set_ylabel("Lines of Code", color="purple")
        ax_right.tick_params(axis='y', labelcolor="purple")

        ax_right.annotate(f'{load_lines[-1]}',
                          xy=(len(versions)-1, load_lines[-1]),
                          xytext=(10, -10), textcoords='offset points',
                          color="purple", fontsize=9,
                          arrowprops=dict(arrowstyle="->", color="purple"))

        ax_left.legend(loc="upper left", fontsize=10, bbox_to_anchor=(0, 1.12))
        ax_right.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1, 1.12))

        plt.title("Load Modules Evolution: File Count & Lines of Code", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 3: Core References Evolution per File
        skip_if_ref_under = 3
        excluded_files = []
        fig, ax = plt.subplots(figsize=(15, 8))
        for file, refs in core_refs_by_file.items():
            if refs[-1] <= skip_if_ref_under:
                excluded_files.append(f"{file} ({refs[-1]})")
                continue
            ax.plot(versions, refs, marker="o", label=file)
        ax.set_ylabel("Core References Count")
        ax.set_xlabel("Versions")
        ax.set_xticks(range(len(versions)))
        ax.set_xticklabels(versions, rotation=90, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.1)
        ax.set_xlim([-0.5, len(versions) + 20])  # Extend x-axis to make space for annotations
        # Annotate the last data point of each file with its filename and value
        for file, refs in core_refs_by_file.items():
            last_index = len(versions) - 1
            last_value = refs[-1]
            if last_value <= skip_if_ref_under:
                continue
            ax.annotate(f"{file} ({last_value})",
                        xy=(last_index, last_value),
                        xytext=(15, 0), textcoords='offset points',
                        fontsize=8, color='white',
                        verticalalignment='center', horizontalalignment='left')
        # Display excluded files list
        if excluded_files:
            excluded_text = "\n".join(excluded_files)
            ax.text(len(versions) + 10, max(max(core_refs_by_file.values(), key=max)) / 4,
                    f"Excluded Files:\n{excluded_text}", fontsize=8, color='white',
                    verticalalignment='center', horizontalalignment='left')
        plt.title("Core References Evolution Per File", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 4: Core and Load Scores
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(versions, core_scores, label="Core Score", color="brown", marker="o")
        ax.plot(versions, load_scores, label="Load Score", color="grey", marker="x")
        ax.set_ylabel("Scores")
        ax.set_xlabel("Versions")
        ax.set_xticks(range(len(versions)))
        ax.set_xticklabels(versions, rotation=90, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.1)
        ax.legend(loc="upper center", fontsize=10, bbox_to_anchor=(0.5, 1.12), ncol=2)

        for idx, version in enumerate(versions):
            if version in highlighted_versions:
                ax.axvline(x=idx, color=DARK_YELLOW, linestyle="--", alpha=0.7)

        plt.title("Pylint Scores Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 5: Dependency Warnings
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(versions, dependency_warnings, label="Dependency Warnings", color="brown", marker="o")
        ax.set_ylabel("Warnings")
        ax.set_xlabel("Versions")
        ax.set_xticks(range(len(versions)))
        ax.set_xticklabels(versions, rotation=90, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.1)
        ax.legend(loc="upper center", fontsize=10, bbox_to_anchor=(0.5, 1.12), ncol=2)

        plt.title("Load Dependency Warnings Evolution", fontweight="bold", fontsize=TITLE_FONT_SIZE)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


        #########################################################
        # Plot 6: Commit Log (Table fitted to page height with text truncation)
        wrap_width = 105  # Maximum characters per line for wrapping
        max_lines = 1    # Maximum number of lines allowed per commit message cell
        meta_data = meta_data[-MAX_COMMIT_HISTORY:] # Set last 40 lines of comments
        table_data = [["Version", "Commit ID", "Message"]]
        for entry in meta_data:
            truncated_message = truncate_message(entry["message"], wrap_width, max_lines)
            table_data.append([entry["version"], entry["commit_id"], truncated_message])

        num_rows = len(table_data)

        # Set figure size to fill most of the PDF page (adjust as needed)
        fig, ax = plt.subplots(figsize=(15, 11))
        ax.axis('off')  # Hide axes for a clean table look

        # Create the table; using loc='center' so we can later force cell heights
        table = ax.table(cellText=table_data,
                         loc='center',
                         cellLoc='left',
                         colWidths=[0.06, 0.3, 0.64])

        # Force a fixed font size for clarity
        font_size = 12 if len(meta_data) < 10 else 10
        table.auto_set_font_size(False)
        table.set_fontsize(font_size)

        # Adjust each cell’s height so that the table fits the full page height.
        # We leave a small vertical margin (here 0.90 of the figure height is used for the table).
        cell_height = 1 / num_rows
        for key, cell in table.get_celld().items():
            cell.set_height(cell_height)
            cell.set_edgecolor("gray")
            cell.get_text().set_color("white")
            # Header formatting
            if key[0] == 0:
                cell.set_facecolor("#404040")
                cell.set_text_props(weight="bold")
            else:
                cell.set_facecolor("#202020")

        # Adjust margins so that the table fills the entire figure height.
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.title(f"Version Commit History (last {MAX_COMMIT_HISTORY})", fontweight="bold", fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

def main():
    input_folder = "./analysis_workdir"  # Change to your folder path
    output_pdf = "timeline_visualization.pdf"

    # Load data
    data = load_json_files(input_folder)
    meta_data = load_meta_files(input_folder)
    release_versions = load_release_versions(input_folder)

    # Visualize data
    visualize_timeline(data, meta_data, release_versions, output_pdf)
    print(f"Timeline visualization saved to {output_pdf}")

if __name__ == "__main__":
    main()
