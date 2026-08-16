"use client";

import React, { useState } from "react";
import { DatasetProfile } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { UploadSection } from "@/components/UploadSection";
import { ProfilingDashboard } from "@/components/ProfilingDashboard";
import { ChatInterface } from "@/components/ChatInterface";

export default function Home() {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const handleProfileLoaded = (newProfile: DatasetProfile, newWarnings?: string[]) => {
    setProfile(newProfile);
    setWarnings(newWarnings || []);
  };

  const handleResetSession = () => {
    setProfile(null);
    setWarnings([]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar
        datasetName={profile?.filename}
        rowCount={profile?.row_count}
        onResetSession={profile ? handleResetSession : undefined}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {!profile ? (
          <UploadSection onProfileLoaded={handleProfileLoaded} />
        ) : (
          <div className="space-y-8">
            {/* Profiling Dashboard Section */}
            <ProfilingDashboard profile={profile} warnings={warnings} />

            {/* Chat Interface Section */}
            <ChatInterface datasetName={profile.filename} />
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-white mt-auto">
        Datavera — Analyse de données en langage naturel (DuckDB & IA) — Projet Portfolio
      </footer>
    </div>
  );
}
