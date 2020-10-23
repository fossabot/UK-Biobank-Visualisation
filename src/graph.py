import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from enum import Enum
from src.dataset_gateway import DatasetGateway, Query, field_id_meta_data, data_encoding_meta_data
from src.tree.node import NodeIdentifier
from src.tree.node_utils import get_field_names_to_inst

def has_multiple_instances(meta_ids):
    for i in range(len(meta_ids) - 1):
        diff_inst = (
            NodeIdentifier(meta_ids[i]).instance_id
            != NodeIdentifier(meta_ids[i + 1]).instance_id
        )
        if diff_inst:
            return True
    return False


def has_array_items(meta_ids):
    if len(meta_ids) <= 1:
        return False
    return NodeIdentifier(meta_ids[0]).part_id != NodeIdentifier(meta_ids[1]).part_id


class Graph:
    def __init__(self):
        self.field_names_to_inst = get_field_names_to_inst()
        self.field_names_to_ids = self.field_names_to_inst.loc[
            self.field_names_to_inst["InstanceID"].isnull()
        ][["FieldID", "NodeName"]].dropna(how="any", axis=0)
        self.field_names_to_ids["FieldID"] = self.field_names_to_ids["FieldID"].apply(
            lambda field_id: str(int(field_id))
        )
        pd.set_option("display.max_rows", None, "display.max_columns", None)

    def get_field_name(self, field_id):
        return self.field_names_to_ids.loc[
            self.field_names_to_ids["FieldID"] == field_id, "NodeName"
        ].item()

    def get_field_instance_map(self, has_instances, has_array):
        def get_field_instance_name(meta_id):
            meta_id = NodeIdentifier(meta_id)
            field_id = meta_id.field_id
            inst_id = meta_id.instance_id
            df_with_name = (
                self.field_names_to_inst.loc[
                    (self.field_names_to_inst["FieldID"] == field_id)
                    & (self.field_names_to_inst["InstanceID"] == inst_id)
                ]["NodeName"]
                if has_instances
                else self.field_names_to_inst.loc[
                    (self.field_names_to_inst["FieldID"] == field_id)
                ]["NodeName"]
            )
            if has_array:
                part_id = meta_id.part_id
                return df_with_name.item() + "[" + str(part_id) + "]"
            return df_with_name.item()

        return get_field_instance_name

    def violin_plot(self, node_id: NodeIdentifier, filtered_data: pd.DataFrame):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for col in filtered_data:
            trace = go.Violin(
                y=filtered_data[col],
                name=col,
                box_visible=True,
                line_color="black",
                meanline_visible=True,
                fillcolor="lightseagreen",
                opacity=0.6,
            )
            fig.add_trace(trace)
        return self.format_graph(fig, node_id, False)

    def scatter_plot(self, node_id: NodeIdentifier, filtered_data: pd.DataFrame):
        fig = px.scatter(data_frame=filtered_data)
        return self.format_graph(fig, node_id, False)

    def bar_plot(self, node_id: NodeIdentifier, filtered_data: pd.DataFrame):
        processed_df = to_categorical_data(node_id, filtered_data)
        fig = px.bar(processed_df, x='categories', y='count')
        return self.format_graph(fig, node_id, False)

    def pie_plot(self, node_id: NodeIdentifier, filtered_data: pd.DataFrame):
        processed_df = to_categorical_data(node_id, filtered_data)
        fig = px.pie(processed_df, names='categories', values='count')
        return self.format_graph(fig, node_id, True)

    def format_graph(self, fig, node_id, showlegend) :
        fig.update_layout(
            title={
                "text": self.get_field_name(node_id.field_id),
                "y": 0.95,
                "x": 0.475,
                "xanchor": "center",
                "yanchor": "top",
            },
            showlegend=showlegend,
        )
        return fig

def get_field_plot(raw_id, graph_type):
    """Returns a graph containing columns of the same field"""
    node_id = NodeIdentifier(raw_id)
    filtered_data = DatasetGateway.submit(Query.from_identifier(node_id))
    # initialise figure
    graph = Graph()

    switcher = {
        1: graph.violin_plot,
        2: graph.scatter_plot,
        3: graph.bar_plot,
        4: graph.pie_plot
    }

    fig = switcher[graph_type](node_id, filtered_data)
    return fig

def to_categorical_data(node_id, filtered_data):
    # Convert categorical data into a bar plot
    field_id_meta = field_id_meta_data()
    encoding_id = int(field_id_meta.loc[field_id_meta["field_id"] == str(node_id.field_id)]["encoding_id"].values[0])
    encoding_dict = data_encoding_meta_data(encoding_id)
    count_dict = dict()

    for ind in filtered_data.index:
        curr_encoding =  filtered_data[node_id.db_id()][ind]
        count_dict[curr_encoding] = count_dict.get(curr_encoding, 0) + 1

    category_list = []
    count_list = []

    for key in encoding_dict:
        category_list.append(encoding_dict[key])
        count_list.append(count_dict[key])

    data = {'categories': category_list, 'count': count_list}

    return pd.DataFrame(data, columns=['categories', 'count'])

class ValueType(Enum):
    INTEGER = (11, "Integer", [1, 2])
    CAT_SINGLE = (21, "Categorical (single)", [3, 4])
    CAT_MULT = (22, "Categorical (multiple)", [3, 4])
    CONT = (31, "Continuous", [1, 2])
    TEXT = (41, "Text", [])
    DATE = (51, "Date", [])
    TIME = (61, "Time", [])
    COMPOUND = (101, "Compound", [])

    def __init__(self, type_id, label, supported_graphs):
        self.type_id = type_id
        self.label = label
        self.supported_graphs = supported_graphs

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        obj._all_values = values
        return obj

    def __repr__(self):
        return "<%s.%s: %s>" % (
            self.__class__.__name__,
            self._name_,
            ", ".join([repr(v) for v in self._all_values]),
        )
