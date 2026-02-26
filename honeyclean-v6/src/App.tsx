import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "./store/useStore";
import { useGPU } from "./hooks/useGPU";
import { useWorker } from "./hooks/useWorker";
import { HoneyBackground } from "./components/HoneyBackground";
import { HoneyCursor } from "./components/HoneyCursor";
import { Layout } from "./components/Layout";
import { ToastContainer } from "./components/Toast";
import { EulaModal } from "./components/EulaModal";
import { FirstRunModal } from "./components/FirstRunModal";
import { QueuePage } from "./pages/QueuePage";
import { EditorPage } from "./pages/EditorPage";
import { ModelsPage } from "./pages/ModelsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AboutPage } from "./pages/AboutPage";

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

const pages: Record<string, () => React.JSX.Element> = {
  queue: QueuePage,
  editor: EditorPage,
  models: ModelsPage,
  settings: SettingsPage,
  about: AboutPage,
};

export default function App() {
  const page = useStore((s) => s.page);
  const eulaAccepted = useStore((s) => s.eulaAccepted);
  const setEulaAccepted = useStore((s) => s.setEulaAccepted);
  const showFirstRun = useStore((s) => s.showFirstRun);
  const setShowFirstRun = useStore((s) => s.setShowFirstRun);
  const setConfig = useStore((s) => s.setConfig);
  const setLanguage = useStore((s) => s.setLanguage);
  const workerReady = useStore((s) => s.workerReady);
  const { send } = useWorker();

  // Poll GPU info
  useGPU(2000);

  // Load config on worker ready
  useEffect(() => {
    if (!workerReady) return;
    send("get_config").then((res) => {
      if (res.status === "ok" && res.data?.config) {
        const cfg = res.data.config as Record<string, unknown>;
        setConfig(cfg);
        if (cfg.language) setLanguage(cfg.language as "en" | "de" | "fr" | "es" | "zh");
        if (cfg.eula_accepted) setEulaAccepted(true);
      }
    }).catch(() => {});
  }, [workerReady, send, setConfig, setLanguage, setEulaAccepted]);

  const PageComponent = pages[page] || QueuePage;

  return (
    <>
      <HoneyBackground />
      <HoneyCursor />

      {!eulaAccepted ? (
        <EulaModal
          onAccept={() => {
            setEulaAccepted(true);
            setShowFirstRun(true);
            send("save_config", {
              config: {
                eula_accepted: true,
                eula_accepted_date: new Date().toISOString(),
              },
            }).catch(() => {});
          }}
        />
      ) : showFirstRun ? (
        <FirstRunModal onClose={() => setShowFirstRun(false)} />
      ) : (
        <Layout>
          <AnimatePresence mode="wait">
            <motion.div
              key={page}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <PageComponent />
            </motion.div>
          </AnimatePresence>
        </Layout>
      )}

      <ToastContainer />
    </>
  );
}
