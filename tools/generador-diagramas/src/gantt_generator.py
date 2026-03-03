#!/usr/bin/env python3
"""
Gantt Chart Generator
Generates Gantt charts for project visualization using GitHub Projects V2 fields
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from typing import List, Optional
import os
import networkx as nx
import graphviz

# Import from github_api.py
from github_api import GitHubIssue, GitHubMilestone


class GanttChartGenerator:
    """Generator for Gantt visualization charts"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style and font
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Try to use Inter font if available
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica', 'sans-serif']

    def create_gantt_chart(self, issues: List[GitHubIssue], milestone: Optional[GitHubMilestone] = None,
                           filename: str = None):
        """
        Create a Gantt chart using the Projects V2 custom fields
        (early_start, early_finish, late_start, late_finish, priority)
        
        Args:
            issues: All issues with populated Projects V2 fields
            milestone: Optional milestone to filter issues by
            filename: Output filename
        """
        # Set filename if none
        if not filename:
            if milestone:
                filename = f"diagrama_gantt_{milestone.number}.png"
            else:
                filename = "diagrama_gantt_general.png"
            
        # Filter issues that have at least early_start and early_finish
        gantt_issues = [
            i for i in issues 
            if i.early_start and i.early_finish
        ]
        
        if milestone:
            gantt_issues = [i for i in gantt_issues if i.milestone == milestone.title]
        
        if not gantt_issues:
            print("No issues with early_start/early_finish fields found for Gantt chart.")
            return

        # Sort issues primarily by early start date
        gantt_issues.sort(key=lambda x: datetime.fromisoformat(x.early_start))
        
        fig, ax = plt.subplots(figsize=(16, max(8, len(gantt_issues) * 0.8)))
        
        y_ticks = []
        y_labels = []
        
        # Priority colors mapping (Modern Tailwind-like coords)
        priority_colors = {
            'baja': ('#10b981', '#047857', '#064e3b'),      # Emerald Green 500 / 700 / 900
            'low': ('#10b981', '#047857', '#064e3b'),
            'media': ('#f59e0b', '#b45309', '#78350f'),     # Amber Orange 500 / 700 / 900
            'medium': ('#f59e0b', '#b45309', '#78350f'),
            'alta': ('#ef4444', '#b91c1c', '#7f1d1d'),      # Rose Red 500 / 700 / 900
            'high': ('#ef4444', '#b91c1c', '#7f1d1d')
        }
        
        # Track min/max dates for plotting range
        min_date = None
        max_date = None
        
        # We'll plot from top to bottom
        for idx, issue in enumerate(gantt_issues):
            y_pos = len(gantt_issues) - idx - 1
            y_ticks.append(y_pos)
            
            title_truncated = issue.title[:45] + '...' if len(issue.title) > 45 else issue.title
            y_labels.append(title_truncated)
            
            es_dt = datetime.fromisoformat(issue.early_start).replace(hour=0, minute=0, second=0, microsecond=0)
            ef_dt = datetime.fromisoformat(issue.early_finish).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # If early finish is the same as early start, give it at least 1 day width for visibility
            if es_dt == ef_dt:
                ef_dt += timedelta(days=1)
                
            duration = (ef_dt - es_dt).days
            
            # Determine color based on priority
            p_color, p_color_dark, p_color_darker = ('#3b82f6', '#1d4ed8', '#1e3a8a') # Default blue (Blue 500 / 700 / 900)
            if issue.priority:
                p_key = issue.priority.lower()
                p_color, p_color_dark, p_color_darker = priority_colors.get(p_key, (p_color, p_color_dark, p_color_darker))
                
            # Box 1: Early start to early finish
            ax.barh(y_pos, duration, left=es_dt, height=0.4, color=p_color, edgecolor='none')
            
            # Track end date for this specific task and slack calculation
            task_end_dt = ef_dt
            
            # The definition of slack (holgura) is Late Start - Early Start
            slack_days = 0
            if issue.late_start:
                ls_dt = datetime.fromisoformat(issue.late_start).replace(hour=0, minute=0, second=0, microsecond=0)
                if ls_dt > es_dt:
                    slack_days = (ls_dt - es_dt).days
            
            # Box 2 & 3: Late bounds
            if issue.late_start and issue.late_finish:
                ls_dt = datetime.fromisoformat(issue.late_start).replace(hour=0, minute=0, second=0, microsecond=0)
                lf_dt = datetime.fromisoformat(issue.late_finish).replace(hour=0, minute=0, second=0, microsecond=0)
                if ls_dt == lf_dt:
                    lf_dt += timedelta(days=1)
                
                # Box 2: Early finish to late start (Visualizing late area before late start)
                if ls_dt > ef_dt:
                    ax.barh(y_pos, (ls_dt - ef_dt).days, left=ef_dt, height=0.4, color=p_color_dark, edgecolor='none')
                    
                # Box 3: Late start to late finish (Tiempo Tardio -> Más oscuro aún)
                start_box3 = max(ls_dt, ef_dt)
                if lf_dt > start_box3:
                    box3_dur = (lf_dt - start_box3).days
                    ax.barh(y_pos, box3_dur, left=start_box3, height=0.4, color=p_color_darker, edgecolor='none')
                
                if lf_dt > task_end_dt:
                    task_end_dt = lf_dt
                
                # Update global range (Only extend max_date, late_start shouldn't push min_date back)
                if not max_date or lf_dt > max_date: max_date = lf_dt
            
            # Annotation for Duration and Slack
            est_dur = duration  # fallback to basic duration
            if issue.estimated_duration:
                est_dur = int(issue.estimated_duration) if issue.estimated_duration == int(issue.estimated_duration) else issue.estimated_duration
            
            day_str = "día" if est_dur == 1 else "días"
            annotation_text = f"{est_dur} {day_str}"
            
            annotation_text += f" ({slack_days}d holgura)"
                
            # Place text cleanly to the right of the latest bar
            label_x = task_end_dt + timedelta(days=0.2)
            ax.text(label_x, y_pos, annotation_text, va='center', ha='left', fontsize=9, color='#4b5563', fontweight='500', 
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
            
            # Update global range
            if not min_date or es_dt < min_date: min_date = es_dt
            if not max_date or task_end_dt > max_date: max_date = task_end_dt
                
        # Set axis formatting
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        # Draw vertical lines for the milestone
        if milestone and milestone.due_on:
            due_date = datetime.fromisoformat(milestone.due_on.replace('Z', '+00:00')).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            
            # Extend global range to include milestone if necessary
            if not min_date or due_date < min_date:
                min_date = due_date
            if not max_date or due_date > max_date:
                max_date = due_date
                
            ax.axvline(x=due_date, color='#e74c3c', linestyle='--', alpha=0.8, linewidth=2)
            ax.text(due_date, len(gantt_issues) + 0.2, milestone.title, 
                    rotation=45, va='bottom', ha='left', color='#e74c3c', fontsize=10, fontweight='bold')
                            
        # Configure X-axis showing dates (after potentially updating min_date/max_date)
        if min_date and max_date:
            import matplotlib.dates as mdates
            # Minimal buffer to not show excessive days after the project ends
            ax.set_xlim(min_date - timedelta(days=1), max_date + timedelta(days=1))
            
            # Add major ticks every 2 days for the labels
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            
            # Add minor ticks every 1 day for the grid lines
            ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
            
            # Optional: Rotate x-ticks for better readability depending on duration
            plt.xticks(rotation=45, ha='right')
        
        # Legend for priorities and time phases (2 rows x 3 columns)
        legend_patches = [
            mpatches.Patch(color='#ef4444', label='Prioridad Alta'),
            mpatches.Patch(facecolor='white', edgecolor='#64748b', hatch='///', label='Tono Claro: Tiempo Temprano'),
            
            mpatches.Patch(color='#f59e0b', label='Prioridad Media'),
            mpatches.Patch(facecolor='#334155', edgecolor='none', label='Tono Oscuro: Holgura'),
            
            mpatches.Patch(color='#10b981', label='Prioridad Baja'),
            mpatches.Patch(facecolor='#0f172a', edgecolor='none', label='Tono Más Oscuro: Tiempo Tardío')
        ]
        # Move legend to the bottom (below the x-axis)
        ax.legend(handles=legend_patches, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        
        # Enable grid for both major (labels) and minor (ticks without labels) to show daily lines
        ax.grid(True, which='major', alpha=0.4, axis='x', color='gray', linestyle='-')
        ax.grid(True, which='minor', alpha=0.2, axis='x', color='gray', linestyle='--')

        # Title positioned at the very top and bolder
        title_str = f'{milestone.title}' if milestone else 'Diagrama de Gantt'
        fig.suptitle(title_str, fontsize=22, fontweight='bold', y=0.98)
        
        plt.subplots_adjust(left=0.2, right=0.95, top=0.85 if milestone else 0.9, bottom=0.3)
        
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved Gantt chart: {output_path}")

    def create_pert_chart(self, issues: List[GitHubIssue], milestone: Optional[GitHubMilestone] = None,
                          filename: str = None):
        """
        Create a PERT chart (Project Evaluation and Review Technique) using graphviz
        """
        import textwrap
        
        if not filename:
            filename = "diagrama_pert"
        else:
            # Graphviz adds the extension itself, so strip .png if present
            if filename.endswith(".png"):
                filename = filename[:-4]
            
        # Filter issues by milestone if provided
        sprint_issues = issues
        if milestone:
            sprint_issues = [i for i in issues if i.milestone == milestone.title]
            
        if not sprint_issues:
            print(f"No issues found for PERT chart {filename}")
            return
            
        dot = graphviz.Digraph(comment='PERT Chart', format='png')
        dot.attr(rankdir='TB')
        
        # Añadir título del Milestone (si lo hay) en la cabecera
        if milestone:
            dot.attr(label=milestone.title, labelloc='t', fontsize='20', fontname='Inter')
            
        dot.attr(nodesep='0.5', ranksep='0.8')
        dot.attr('node', shape='none', fontname='Inter', margin='0')
        
        colors_map = {
            "Alta": "#ef4444",      
            "Media": "#f59e0b",     
            "Baja": "#10b981",      
        }
        
        issue_map = {issue.number: issue for issue in sprint_issues}
        
        # 1. Build Edges First
        edges = []
        linked_nodes = set()
        for issue in sprint_issues:
            if getattr(issue, "blocking", None):
                for blocked_num in issue.blocking:
                    if blocked_num in issue_map:
                        edges.append((str(issue.number), str(blocked_num)))
                        linked_nodes.add(str(issue.number))
                        linked_nodes.add(str(blocked_num))
                        
            if getattr(issue, "blocked_by", None):
                for blocker_num in issue.blocked_by:
                    if blocker_num in issue_map:
                        edges.append((str(blocker_num), str(issue.number)))
                        linked_nodes.add(str(blocker_num))
                        linked_nodes.add(str(issue.number))
                        
            if getattr(issue, "parent_number") and issue.parent_number in issue_map:
                edges.append((str(issue.parent_number), str(issue.number)))
                linked_nodes.add(str(issue.parent_number))
                linked_nodes.add(str(issue.number))
                
        # Remove duplicates
        edges = list(set(edges))

        # 2. Critical Path Method (CPM) Calculation
        nodes_str = {str(iss.number) for iss in sprint_issues}
        adj = {n: [] for n in nodes_str}
        rev_adj = {n: [] for n in nodes_str}
        
        for src, dst in edges:
            if src in nodes_str and dst in nodes_str:
                adj[src].append(dst)
                rev_adj[dst].append(src)
                
        # Topological Sort
        in_degree = {n: len(rev_adj[n]) for n in nodes_str}
        queue = [n for n in nodes_str if in_degree[n] == 0]
        topo_order = []
        while queue:
            u = queue.pop(0)
            topo_order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        # Handle cycles (fallback append remaining)
        for n in nodes_str:
            if n not in topo_order:
                topo_order.append(n)

        # Durations
        durations = {}
        for iss in sprint_issues:
            d = getattr(iss, "estimated_duration", 1)
            try:
                d = float(d)
            except:
                d = 1.0
            durations[str(iss.number)] = d

        # Forward Pass
        es_cpm = {n: 0.0 for n in nodes_str}
        ef_cpm = {n: 0.0 for n in nodes_str}
        for u in topo_order:
            max_es = 0.0
            for p in rev_adj[u]:
                if ef_cpm[p] > max_es:
                    max_es = ef_cpm[p]
            es_cpm[u] = max_es
            ef_cpm[u] = max_es + durations[u]
            
        project_duration = max(ef_cpm.values()) if ef_cpm else 0.0
        
        # Backward Pass
        ls_cpm = {n: 0.0 for n in nodes_str}
        lf_cpm = {n: project_duration for n in nodes_str}
        for u in reversed(topo_order):
            min_lf = project_duration
            if adj[u]:
                min_lf = min(ls_cpm[s] for s in adj[u])
            lf_cpm[u] = min_lf
            ls_cpm[u] = min_lf - durations[u]
            
        # Compute Slack and Critical Edges
        cpm_slack = {n: ls_cpm[n] - es_cpm[n] for n in nodes_str}
        critical_edges = set()
        for u in nodes_str:
            for v in adj[u]:
                # Edge is critical if both nodes have 0 slack AND it's a driving dependency
                if abs(cpm_slack[u]) < 0.1 and abs(cpm_slack[v]) < 0.1:
                    if abs(ef_cpm[u] - es_cpm[v]) < 0.1:
                        critical_edges.add((u, v))

        # 3. Create Node Labels
        for issue in sprint_issues:
            iss_id = str(issue.number)
            slack_days = int(cpm_slack.get(iss_id, 0))
            is_critical = slack_days == 0
            
            p = getattr(issue, "priority", "Media")
            if not p:
                p = "Media"
            bg_color = colors_map.get(p, "#9ca3af")
            
            wrapped_title_lines = textwrap.wrap(issue.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), width=15)
            wrapped_title = "<BR/>".join(wrapped_title_lines)
            
            # Formatear fechas a Día-Mes (ej. 2-Feb)
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            def format_date(d_str):
                if not d_str:
                    return "--/--"
                try:
                    parts = d_str[:10].split('-')
                    if len(parts) == 3:
                        d = int(parts[2])
                        m = int(parts[1])
                        return f"{d}-{meses[m-1]}"
                except:
                    pass
                return "--/--"
                
            es = format_date(getattr(issue, "early_start", None))
            ef = format_date(getattr(issue, "early_finish", None))
            ls = format_date(getattr(issue, "late_start", None))
            lf = format_date(getattr(issue, "late_finish", None))
            
            dur = getattr(issue, "estimated_duration", "?")
            if dur != "?": 
                if isinstance(dur, float) and dur.is_integer():
                    dur = int(dur)
                dur = f"{dur}d"
                
            label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">
  <TR>
    <TD BORDER="2" COLOR="{bg_color}" BGCOLOR="{bg_color}">
      <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{bg_color}">
        <TR>
          <TD ALIGN="LEFT"><FONT COLOR="white" POINT-SIZE="10">{es}</FONT></TD>
          <TD ALIGN="CENTER"> </TD>
          <TD ALIGN="RIGHT"><FONT COLOR="white" POINT-SIZE="10">{ef}</FONT></TD>
        </TR>
        <TR>
          <TD COLSPAN="3" ALIGN="CENTER"><FONT COLOR="white" POINT-SIZE="12">{wrapped_title}</FONT></TD>
        </TR>
        <TR>
          <TD ALIGN="LEFT"><FONT COLOR="white" POINT-SIZE="10">{ls}</FONT></TD>
          <TD ALIGN="CENTER"> </TD>
          <TD ALIGN="RIGHT"><FONT COLOR="white" POINT-SIZE="10">{lf}</FONT></TD>
        </TR>
      </TABLE>
    </TD>
  </TR>
  <TR>
    <TD ALIGN="CENTER" BORDER="0"><FONT COLOR="#4b5563" POINT-SIZE="9">D: {dur} - H: {slack_days}d</FONT></TD>
  </TR>
</TABLE>>'''
            issue.temp_gv_label = label

        # Separate nodes
        unlinked_issues = [iss for iss in sprint_issues if str(iss.number) not in linked_nodes]
        linked_issues = [iss for iss in sprint_issues if str(iss.number) in linked_nodes]
        
        # Add linked nodes to main graph
        for iss in linked_issues:
            dot.node(str(iss.number), label=iss.temp_gv_label)
            
        # Group unlinked nodes in a subgraph at the bottom
        if unlinked_issues:
            with dot.subgraph(name='cluster_unlinked') as c:
                c.attr(style='invis') # Hide cluster box
                for iss in unlinked_issues:
                    c.node(str(iss.number), label=iss.temp_gv_label)
                    
            # To force them down, add an invisible edge from one of the linked nodes (leaves) to the unlinked subgraph
            # Find leaves (nodes with no outgoing edges)
            sources = set(src for src, dst in edges)
            leaves = [node for node in linked_nodes if node not in sources]
            
            if leaves and unlinked_issues:
                # Add invis edge from first leaf to first unlinked
                dot.edge(leaves[0], str(unlinked_issues[0].number), style='invis')

        for src, dst in edges:
            if (src, dst) in critical_edges:
                # Add Label to Critical Path
                dot.edge(src, dst, color="#dc2626", penwidth="3.5", fontcolor="#dc2626", fontsize="10", fontname="Inter") # Red and thicker
            else:
                dot.edge(src, dst, color="#4b5563", penwidth="2.5")
            
        # Add Legend as a disconnected node or subgraph
        dot.attr('node', shape='none')
        legend_label = '''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">
  <TR><TD ALIGN="CENTER" BORDER="0"><FONT COLOR="#374151" POINT-SIZE="11"><B>Leyenda Nodos</B></FONT></TD></TR>
  <TR><TD BORDER="2" COLOR="#9ca3af" BGCOLOR="white">
    <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
      <TR>
        <TD ALIGN="LEFT"><FONT COLOR="#374151" POINT-SIZE="10">I. Tmp</FONT></TD>
        <TD ALIGN="CENTER"><FONT COLOR="#374151" POINT-SIZE="10">     </FONT></TD>
        <TD ALIGN="RIGHT"><FONT COLOR="#374151" POINT-SIZE="10">F. Tmp</FONT></TD>
      </TR>
      <TR><TD COLSPAN="3" ALIGN="CENTER"><FONT COLOR="#374151" POINT-SIZE="12">Título Tarea</FONT></TD></TR>
      <TR>
        <TD ALIGN="LEFT"><FONT COLOR="#374151" POINT-SIZE="10">I. Tar</FONT></TD>
        <TD ALIGN="CENTER"><FONT COLOR="#374151" POINT-SIZE="10">    </FONT></TD>
        <TD ALIGN="RIGHT"><FONT COLOR="#374151" POINT-SIZE="10">F. Tar</FONT></TD>
      </TR>
    </TABLE>
  </TD></TR>
  <TR>
    <TD ALIGN="CENTER" BORDER="0"><FONT COLOR="#4b5563" POINT-SIZE="9">Duración - Holgura</FONT></TD>
  </TR>
  <TR>
    <TD BORDER="0" ALIGN="CENTER">
       <FONT COLOR="#dc2626" POINT-SIZE="10"><B>Camino Crítico</B></FONT>
    </TD>
  </TR>
</TABLE>>'''
        dot.node("legend", label=legend_label)
        
        p_legend_label = '''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">
  <TR><TD BORDER="2" COLOR="#9ca3af" BGCOLOR="white">
    <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="4" CELLPADDING="2">
      <TR><TD COLSPAN="2" ALIGN="CENTER"><FONT COLOR="#374151" POINT-SIZE="11"><B>Prioridades</B></FONT></TD></TR>
      <TR><TD BGCOLOR="#ef4444" WIDTH="15"></TD><TD ALIGN="LEFT"><FONT COLOR="#374151" POINT-SIZE="10">Alta</FONT></TD></TR>
      <TR><TD BGCOLOR="#f59e0b" WIDTH="15"></TD><TD ALIGN="LEFT"><FONT COLOR="#374151" POINT-SIZE="10">Media</FONT></TD></TR>
      <TR><TD BGCOLOR="#10b981" WIDTH="15"></TD><TD ALIGN="LEFT"><FONT COLOR="#374151" POINT-SIZE="10">Baja</FONT></TD></TR>
    </TABLE>
  </TD></TR>
</TABLE>>'''
        dot.node("p_legend", label=p_legend_label)

        # Render
        save_path = os.path.join(self.output_dir, filename)
        dot.render(save_path, cleanup=True)
        print(f"Saved PERT chart: {save_path}.png")
