"use client";

import React, { useState } from "react";
import { DatasetProfile } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { UploadSection } from "@/components/UploadSection";
import { ProfilingDashboard } from "@/components/ProfilingDashboard";
import { ChatInterface } from "@/components/ChatInterface";
import { ManualExploration } from "@/components/ManualExploration";
import { MessageSquare, BarChart3, Database } from "lucide-react";

export default function Home() {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "explore" | "profile">("chat");

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
          <div className="space-y-6">
            {/* View Switcher Tabs */}
            <div className="flex border-b border-slate-200 bg-white rounded-xl p-1.5 shadow-sm border">
              <button
                onClick={() => setActiveTab("chat")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === "chat"
                    ? "bg-brand-50 text-brand-700 shadow-sm"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                <span>Assistant IA & Chat</span>
              </button>

              <button
                onClick={() => setActiveTab("explore")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === "explore"
                    ? "bg-brand-50 text-brand-700 shadow-sm"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Exploration Graphique (16 Types)</span>
              </button>

              <button
                onClick={() => setActiveTab("profile")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === "profile"
                    ? "bg-brand-50 text-brand-700 shadow-sm"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Database className="w-4 h-4" />
                <span>Aperçu & Profilage des Données</span>
              </button>
            </div>

            {/* Active View Content */}
            {activeTab === "chat" && <ChatInterface datasetName={profile.filename} />}

            {activeTab === "explore" && (
              <ManualExploration
                profile={profile}
                onProfileUpdate={(newProf) => setProfile(newProf)}
              />
            )}

            {activeTab === "profile" && (
              <ProfilingDashboard profile={profile} warnings={warnings} />
            )}
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-white mt-auto">
        Datavera — Analyse de données en langage naturel (DuckDB & IA) — Projet Portfolio
      </footer>
    </div>
  );
}
