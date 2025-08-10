import plotly.graph_objects as go
import plotly.io as pio
import json

# Data from the provided JSON
data = {
    "nodes": [
        {"id": "input", "label": "LC Document Input", "type": "input", "color": "#E3F2FD"},
        {"id": "parser", "label": "LC Parser", "type": "process", "color": "#BBDEFB"},
        {"id": "router", "label": "Validation Router", "type": "process", "color": "#BBDEFB"},
        {"id": "orchestrator", "label": "LangGraph Orchestrator", "type": "process", "color": "#90CAF9"},
        {"id": "agent1", "label": "Credit Type Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "agent2", "label": "Date Validation Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "agent3", "label": "Amount Validation Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "agent4", "label": "Document Requirements Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "agent5", "label": "Shipping Terms Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "agent6", "label": "Bank Details Agent", "type": "agent", "color": "#FFE0B2"},
        {"id": "rag", "label": "RAG Knowledge Base", "type": "knowledge", "color": "#C8E6C9"},
        {"id": "ucp600", "label": "UCP600 Vector Store", "type": "storage", "color": "#A5D6A7"},
        {"id": "isbp745", "label": "ISBP745 Vector Store", "type": "storage", "color": "#A5D6A7"},
        {"id": "mappings", "label": "Mappings Store", "type": "storage", "color": "#A5D6A7"},
        {"id": "aggregator", "label": "Results Aggregator", "type": "process", "color": "#D1C4E9"},
        {"id": "generator", "label": "Report Generator", "type": "process", "color": "#D1C4E9"},
        {"id": "output", "label": "Final Validation Report", "type": "output", "color": "#F3E5F5"}
    ],
    "connections": [
        {"from": "input", "to": "parser"},
        {"from": "parser", "to": "router"},
        {"from": "router", "to": "orchestrator"},
        {"from": "orchestrator", "to": "agent1"},
        {"from": "orchestrator", "to": "agent2"},
        {"from": "orchestrator", "to": "agent3"},
        {"from": "orchestrator", "to": "agent4"},
        {"from": "orchestrator", "to": "agent5"},
        {"from": "orchestrator", "to": "agent6"},
        {"from": "agent1", "to": "rag"},
        {"from": "agent2", "to": "rag"},
        {"from": "agent3", "to": "rag"},
        {"from": "agent4", "to": "rag"},
        {"from": "agent5", "to": "rag"},
        {"from": "agent6", "to": "rag"},
        {"from": "rag", "to": "ucp600"},
        {"from": "rag", "to": "isbp745"},
        {"from": "rag", "to": "mappings"},
        {"from": "agent1", "to": "aggregator"},
        {"from": "agent2", "to": "aggregator"},
        {"from": "agent3", "to": "aggregator"},
        {"from": "agent4", "to": "aggregator"},
        {"from": "agent5", "to": "aggregator"},
        {"from": "agent6", "to": "aggregator"},
        {"from": "aggregator", "to": "generator"},
        {"from": "generator", "to": "output"}
    ]
}

# Create strict hierarchical layout with clear vertical separation
positions = {
    # Layer 1: Input (y=10)
    "input": (6, 10),
    
    # Layer 2: Processing (y=8.5, 7, 5.5)
    "parser": (6, 8.5),
    "router": (6, 7),
    "orchestrator": (6, 5.5),
    
    # Layer 3: Agents (y=4) - evenly spaced horizontally
    "agent1": (1, 4),
    "agent2": (2.8, 4),
    "agent3": (4.6, 4),
    "agent4": (6.4, 4),
    "agent5": (8.2, 4),
    "agent6": (10, 4),
    
    # Layer 4: Knowledge (y=2.5)
    "rag": (5.5, 2.5),
    
    # Layer 5: Storage (y=1)
    "ucp600": (3, 1),
    "isbp745": (5.5, 1),
    "mappings": (8, 1),
    
    # Layer 6: Output Processing (y=2.5, 1, -0.5) - vertically aligned
    "aggregator": (8.5, 2.5),
    "generator": (8.5, 1),
    "output": (8.5, -0.5)
}

# Create figure
fig = go.Figure()

# Function to create proper abbreviated labels within 15 char limit
def create_label(original_label):
    if len(original_label) <= 15:
        return original_label
    
    # Specific abbreviations to maintain clarity
    abbreviations = {
        "LC Document Input": "LC Input",
        "Validation Router": "Valid Router", 
        "LangGraph Orchestrator": "LangGraph Orch",
        "Credit Type Agent": "Credit Agent",
        "Date Validation Agent": "Date Agent",
        "Amount Validation Agent": "Amount Agent", 
        "Document Requirements Agent": "Doc Req Agent",
        "Shipping Terms Agent": "Ship Agent",
        "Bank Details Agent": "Bank Agent",
        "RAG Knowledge Base": "RAG Knowledge",
        "UCP600 Vector Store": "UCP600 Store",
        "ISBP745 Vector Store": "ISBP745 Store",
        "Results Aggregator": "Results Agg",
        "Report Generator": "Report Gen", 
        "Final Validation Report": "Final Report"
    }
    
    return abbreviations.get(original_label, original_label[:15])

# Draw connections with minimal overlap
for conn in data["connections"]:
    from_pos = positions[conn["from"]]
    to_pos = positions[conn["to"]]
    
    fig.add_trace(go.Scatter(
        x=[from_pos[0], to_pos[0]],
        y=[from_pos[1], to_pos[1]],
        mode='lines',
        line=dict(color='#555555', width=2),
        showlegend=False,
        hoverinfo='none'
    ))

# Use brand colors in order for node types
type_colors = {
    "input": "#1FB8CD",     # Strong cyan
    "process": "#DB4545",   # Bright red  
    "agent": "#2E8B57",     # Sea green
    "knowledge": "#5D878F", # Cyan
    "storage": "#D2BA4C",   # Moderate yellow
    "output": "#B4413C"     # Moderate red
}

# Create nodes grouped by type with proper colors
node_groups = {
    "input": [],
    "process": [], 
    "agent": [],
    "knowledge": [],
    "storage": [],
    "output": []
}

# Group nodes by type
for node in data["nodes"]:
    node_groups[node["type"]].append(node)

# Add nodes for each type
for node_type, nodes in node_groups.items():
    if not nodes:
        continue
        
    x_vals = []
    y_vals = []
    texts = []
    
    for node in nodes:
        pos = positions[node["id"]]
        x_vals.append(pos[0])
        y_vals.append(pos[1])
        texts.append(create_label(node["label"]))
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers+text',
        marker=dict(
            size=50,  # Larger nodes
            color=type_colors[node_type],
            line=dict(width=3, color='white'),
            opacity=0.9
        ),
        text=texts,
        textposition="middle center",
        textfont=dict(size=11, color='black', family="Arial Black"),
        name=f"{node_type.title()} Layer",
        showlegend=True,
        cliponaxis=False
    ))

# Add layer background rectangles for visual grouping
layer_backgrounds = [
    {"name": "Input Layer", "y": 9.5, "height": 1, "color": "rgba(31, 184, 205, 0.1)"},
    {"name": "Process Layer", "y": 5, "height": 4, "color": "rgba(219, 69, 69, 0.1)"},
    {"name": "Agent Layer", "y": 3.5, "height": 1, "color": "rgba(46, 139, 87, 0.1)"},
    {"name": "Knowledge Layer", "y": 2, "height": 1, "color": "rgba(93, 135, 143, 0.1)"},
    {"name": "Storage Layer", "y": 0.5, "height": 1, "color": "rgba(210, 186, 76, 0.1)"},
    {"name": "Output Layer", "y": -1, "height": 4, "color": "rgba(180, 65, 60, 0.1)"}
]

# Add background rectangles
for bg in layer_backgrounds:
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=11.5,
        y0=bg["y"], y1=bg["y"] + bg["height"],
        fillcolor=bg["color"],
        line=dict(width=0),
        layer="below"
    )

# Update layout
fig.update_layout(
    title="LC Validation System Architecture",
    showlegend=True,
    legend=dict(
        orientation='h',
        yanchor='bottom', 
        y=1.02,
        xanchor='center',
        x=0.5,
        font=dict(size=12)
    ),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='white',
    paper_bgcolor='white'
)

fig.update_xaxes(range=[-1, 12])
fig.update_yaxes(range=[-2, 11])

# Save the chart
fig.write_image("lc_validation_architecture.png", width=1400, height=1000)

print("Professional LC Validation System Architecture diagram created!")