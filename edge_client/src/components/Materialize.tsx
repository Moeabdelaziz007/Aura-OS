/**
 * ✨ AetherOS — Materialize Animation Wrapper
 *
 * Wraps any component with the signature "materialize" animation:
 * Particles scatter → glassmorphic card solidifies from the void.
 *
 * "من العدم، الأثير يُبدع" — From nothing, Aether creates.
 */

import { motion, AnimatePresence } from "framer-motion";
import React from "react";

interface MaterializeProps {
    children: React.ReactNode;
    id: string;
    animation?: string;
    layout?: string;
}

const materializeVariants = {
    hidden: {
        opacity: 0,
        scale: 0.8,
        filter: "blur(12px)",
        y: 30,
    },
    visible: {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        y: 0,
        transition: {
            type: "spring",
            stiffness: 200,
            damping: 20,
            duration: 0.6,
        },
    },
    exit: {
        opacity: 0,
        scale: 0.9,
        filter: "blur(8px)",
        y: -20,
        transition: {
            duration: 0.4,
            ease: "easeInOut",
        },
    },
};

const slideUpVariants = {
    hidden: { opacity: 0, y: 60 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { type: "spring", stiffness: 300, damping: 25 },
    },
    exit: { opacity: 0, y: -40, transition: { duration: 0.3 } },
};

const fadeVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.5 } },
    exit: { opacity: 0, transition: { duration: 0.3 } },
};

const VARIANT_MAP: Record<string, typeof materializeVariants> = {
    materialize: materializeVariants,
    slide_up: slideUpVariants,
    fade: fadeVariants,
};

const LAYOUT_STYLES: Record<string, React.CSSProperties> = {
    card: {},
    fullscreen: {
        position: "fixed",
        inset: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
    sidebar: {
        position: "fixed",
        right: 0,
        top: 0,
        bottom: 0,
        width: "420px",
        zIndex: 90,
    },
    toast: {
        position: "fixed",
        bottom: "24px",
        right: "24px",
        zIndex: 110,
        maxWidth: "360px",
    },
};

export const Materialize: React.FC<MaterializeProps> = ({
    children,
    id,
    animation = "materialize",
    layout = "card",
}) => {
    const variants = VARIANT_MAP[animation] || materializeVariants;
    const layoutStyle = LAYOUT_STYLES[layout] || {};

    return (
        <motion.div
            key={id}
            variants={variants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={layoutStyle}
            className="aether-materialize"
        >
            {children}
        </motion.div>
    );
};
