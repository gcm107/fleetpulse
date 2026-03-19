import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function MainLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#09090b]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area - offset for sidebar */}
      <div className="flex-1 flex flex-col ml-60 min-h-0">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
