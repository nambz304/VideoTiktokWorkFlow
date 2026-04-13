const BASE = "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

// Sessions
export const createSession = (title: string, lang: string) =>
  req<import("./types").Session>("/sessions", {
    method: "POST",
    body: JSON.stringify({ title, lang }),
  });

export const listSessions = () =>
  req<import("./types").Session[]>("/sessions");

export const getSession = (id: number) =>
  req<import("./types").Session>(`/sessions/${id}`);

export const updateSession = (id: number, data: Partial<import("./types").Session>) =>
  req<import("./types").Session>(`/sessions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteSession = (id: number) =>
  req<{ ok: boolean }>(`/sessions/${id}`, { method: "DELETE" });

// Pipeline steps
export const fetchTrends = (sessionId: number) =>
  req<import("./types").TrendTopic[]>(`/sessions/${sessionId}/step/1a`, { method: "POST" });

export const generateScripts = (sessionId: number) =>
  req<{ scripts: string[] }>(`/sessions/${sessionId}/step/1c`, { method: "POST" });

export const splitScenes = (sessionId: number, script: string, characterId?: number) => {
  const body: Record<string, unknown> = { script };
  if (characterId !== undefined) body.character_id = characterId;
  return req<{ scenes: import("./types").Scene[] }>(`/sessions/${sessionId}/step/2`, {
    method: "POST",
    body: JSON.stringify(body),
  });
};

export const assignImages = (sessionId: number) =>
  req<{ scenes: import("./types").Scene[] }>(`/sessions/${sessionId}/step/3`, { method: "POST" });

export const genSceneVideo = (sessionId: number, sceneId: number) =>
  req<{ scene_id: number; video_path: string }>(`/sessions/${sessionId}/step/4/${sceneId}`, { method: "POST" });

export const mergeVideo = (sessionId: number, bgmPath: string, bgmVolume: number) =>
  req<{ final_video_path: string; caption: string; hashtags: string[] }>(
    `/sessions/${sessionId}/step/5`,
    { method: "POST", body: JSON.stringify({ bgm_path: bgmPath, bgm_volume: bgmVolume }) }
  );

// Scenes
export const getScenes = (sessionId: number) =>
  req<import("./types").Scene[]>(`/sessions/${sessionId}/scenes`);

// Assets
export const listMiloImages = (tag?: string) =>
  req<import("./types").MiloImage[]>(`/assets/milo${tag ? `?tag=${tag}` : ""}`);

// Schedule
export const listSchedule = () =>
  req<import("./types").ScheduleEntry[]>("/schedule");

export const createSchedule = (data: {
  session_id: number;
  post_time: string;
  caption?: string;
  hashtags?: string;
}) =>
  req<import("./types").ScheduleEntry>("/schedule", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateSchedule = (id: number, data: Partial<import("./types").ScheduleEntry>) =>
  req<import("./types").ScheduleEntry>(`/schedule/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Characters
export const listCharacters = () =>
  req<{ characters: import("./types").Character[] }>("/characters/");

// Chat
export const sendChat = (sessionId: number, message: string, step: number) =>
  req<{ reply: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message, step }),
  });
