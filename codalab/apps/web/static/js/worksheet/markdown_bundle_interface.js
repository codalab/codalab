/** @jsx React.DOM */

var MarkdownBundle = React.createClass({
    mixins: [CheckboxMixin],
    getInitialState: function(){
        return {
            lines: this.props.item.state.interpreted.split(/\r\n|\r|\n/).length,
            checked: false
        }
    },
    keysToHandle: function(){
        return['esc','enter']
    },
    handleKeydown: function(event){
        var key = keyMap[event.keyCode];
        if(typeof key !== 'undefined'){
            switch (key) {
                case 'esc':
                    this._owner.setState({editingIndex: -1});
                    if(!$(this.getDOMNode()).find('textarea').val().length){
                        this._owner.unInsert();
                    }
                    break;
                case 'enter':
                    if(event.ctrlKey || event.metaKey){
                        event.preventDefault();
                        this.saveEditedItem(event.target);
                    }
                    break;
                default:
                    return true;
            }
        } else {
            return true;
        }
    },
    saveEditedItem: function(textarea){
        this.props.handleSave(textarea);
    },
    componentDidMount: function() {
        MathJax.Hub.Queue([
            'Typeset',
            MathJax.Hub,
            this.getDOMNode()
        ]);
        if(this.props.editing){
            $(this.getDOMNode()).find('textarea').focus();
        }
    },
    componentDidUpdate: function(){
        if(this.props.editing){
            $(this.getDOMNode()).find('textarea').focus();
        }
    },
    handleClick: function(){
        this.props.setFocus(this);
    },
    render: function() {
        var content = this.props.item.state.interpreted;
        var className = 'type-markup' + (this.props.focused ? ' focused' : '');
        var checkbox = this.props.canEdit ? <input type="checkbox" className="ws-checkbox" onChange={this.handleCheck} checked={this.state.checked} /> : null;
        if (this.props.editing){
            return(
                <div className="ws-item" onClick={this.handleClick}>
                    {checkbox}
                    <textarea className={className} rows={this.state.lines} onKeyDown={this.handleKeydown} defaultValue={content} />
                </div>
            )
        }else {
        var text = marked(content);
        // create a string of html for innerHTML rendering
        // more info about dangerouslySetInnerHTML
        // http://facebook.github.io/react/docs/special-non-dom-attributes.html
        // http://facebook.github.io/react/docs/tags-and-attributes.html#html-attributes
        return(
            <div className="ws-item" onClick={this.handleClick}>
                {checkbox}
                <div className={className} dangerouslySetInnerHTML={{__html: text}} onKeyDown={this.handleKeydown} />
            </div>
        );
        }
    } // end of render function
}); //end of  MarkdownBundle