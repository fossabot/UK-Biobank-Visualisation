import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {TreeExample} from "./TreeExample";

export default class HierarchyTree extends Component {
    render() {
        const {id, data, selected, n_updates, setProps} = this.props;
        return (
            <TreeExample id={id} nodes={data} selected={selected} n_updates={n_updates} setProps={setProps} />
        );
    }
}

HierarchyTree.defaultProps = {};

HierarchyTree.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * The data displayed in the tree.
     */
    data: PropTypes.array,

    /**
     * An array of selected FieldIds
     */
    selected: PropTypes.arrayOf(PropTypes.number),

    /**
     * A count of the number of times the inputs have updated, so the callback function knows when to update
     */
    n_updates: PropTypes.number
};
