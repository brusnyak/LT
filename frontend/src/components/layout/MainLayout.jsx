import React from 'react';
import { Outlet } from 'react-router-dom';
import TopBar from './TopBar';
import TabBar from './TabBar';

export default function MainLayout() {
    return (
        <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            <TopBar />
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                <TabBar />
                <main className="main-content" style={{ flex: 1, overflow: 'auto' }}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
