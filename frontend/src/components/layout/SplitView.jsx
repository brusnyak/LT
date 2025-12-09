import React from 'react';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';

export default function SplitView({ topChart, bottomChart }) {
    return (
        <PanelGroup direction="vertical">
            <Panel minSize={30}>
                {topChart}
            </Panel>
            <PanelResizeHandle className="resize-handle" />
            <Panel minSize={30}>
                {bottomChart}
            </Panel>
        </PanelGroup>
    );
}
