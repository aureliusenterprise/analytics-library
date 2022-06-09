from m4i_analytics.graphs.visualisations.LayoutRegistry import LayoutRegistry


if __name__ == '__main__':

    registry = LayoutRegistry()

    layout_names = registry.get_layout_names()

    print(layout_names)
