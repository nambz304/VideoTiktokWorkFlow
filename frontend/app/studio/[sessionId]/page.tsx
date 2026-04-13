"use client";
import { use, useState, useEffect } from "react";
import useSWR from "swr";
import { getSession, updateSession } from "@/lib/api";
import Stepper from "@/components/Stepper";
import ChatSidebar from "@/components/ChatSidebar";
import Step0Character from "@/components/steps/Step0Character";
import Step1Trend from "@/components/steps/Step1Trend";
import Step2Scenes from "@/components/steps/Step2Scenes";
import Step3Images from "@/components/steps/Step3Images";
import Step4Video from "@/components/steps/Step4Video";
import Step5Merge from "@/components/steps/Step5Merge";
import Step6Publish from "@/components/steps/Step6Publish";

export default function StudioPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = use(params);
  const id = parseInt(sessionId);
  const { data: session, mutate } = useSWR(`session-${id}`, () => getSession(id));
  const [showCharPicker, setShowCharPicker] = useState<boolean | null>(null);

  useEffect(() => {
    if (session && showCharPicker === null) {
      setShowCharPicker(session.step === 1 && !session.character_id);
    }
  }, [session, showCharPicker]);

  async function goToStep(n: number) {
    await updateSession(id, { step: n });
    mutate();
  }

  async function handleCharacterAdvance(characterId?: number) {
    if (characterId !== undefined) {
      await updateSession(id, { character_id: characterId });
      mutate();
    }
    setShowCharPicker(false);
  }

  if (!session) return (
    <div className="h-screen bg-gray-950 flex items-center justify-center text-gray-600 text-sm">
      Đang tải session...
    </div>
  );

  const stepComponents: Record<number, React.ReactNode> = {
    1: <Step1Trend session={session} onAdvance={() => goToStep(2)} />,
    2: <Step2Scenes session={session} onAdvance={() => goToStep(3)} onBack={() => goToStep(1)} />,
    3: <Step3Images session={session} onAdvance={() => goToStep(4)} onBack={() => goToStep(2)} />,
    4: <Step4Video session={session} onAdvance={() => goToStep(5)} onBack={() => goToStep(3)} />,
    5: <Step5Merge session={session} onAdvance={() => goToStep(6)} onBack={() => goToStep(4)} />,
    6: <Step6Publish session={session} onBack={() => goToStep(5)} />,
  };

  const activeContent = showCharPicker
    ? <Step0Character session={session} onAdvance={handleCharacterAdvance} />
    : (stepComponents[session.step] ?? <div className="p-6 text-gray-500">Unknown step</div>);

  return (
    <div className="h-screen flex flex-col bg-gray-950 overflow-hidden">
      <div className="flex-shrink-0">
        <div className="px-6 py-2 bg-gray-900 border-b border-gray-800 flex items-center gap-3">
          <a href="/sessions" className="text-xs text-gray-500 hover:text-gray-300">← Sessions</a>
          <span className="text-xs text-gray-700">/</span>
          <span className="text-xs text-gray-300 font-medium">{session.title}</span>
          {session.character_id && (
            <span className="text-xs text-indigo-400 ml-auto">🤖 Nhân vật #{session.character_id}</span>
          )}
        </div>
        <Stepper currentStep={session.step} />
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-hidden flex flex-col">
          {activeContent}
        </div>
        <ChatSidebar sessionId={id} step={session.step} />
      </div>
    </div>
  );
}
