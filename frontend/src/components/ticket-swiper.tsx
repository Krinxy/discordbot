"use client";

import { motion, type PanInfo } from "motion/react";
import { useState } from "react";
import { toast } from "sonner";

import { setTicketStatusAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import type { Ticket, TicketReviewStatus } from "@/lib/admin-api";

const SWIPE_THRESHOLD = 120;
const FLY_OUT_DISTANCE = 500;

type ExitDirection = -1 | 0 | 1;

export function TicketSwiper({ initialQueue }: { initialQueue: Ticket[] }) {
  const [queue, setQueue] = useState(initialQueue);
  const [exitDirection, setExitDirection] = useState<ExitDirection | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  const current = queue[0];
  const stack = queue.slice(1, 3);

  function startExit(direction: ExitDirection) {
    if (exitDirection !== null) return;
    setExitDirection(direction);
  }

  async function finishExit() {
    if (!current || exitDirection === null) return;
    const ticket = current;
    const direction = exitDirection;
    setQueue((prev) => prev.slice(1));
    setExitDirection(null);
    if (direction === 0) return;
    const status: TicketReviewStatus = direction === 1 ? "closed" : "currently_not_possible";
    setIsBusy(true);
    try {
      await setTicketStatusAction(ticket.id, status);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not update the ticket.");
      setQueue((prev) => [ticket, ...prev]);
    } finally {
      setIsBusy(false);
    }
  }

  function handleDragEnd(_event: unknown, info: PanInfo) {
    if (info.offset.x > SWIPE_THRESHOLD) {
      startExit(1);
    } else if (info.offset.x < -SWIPE_THRESHOLD) {
      startExit(-1);
    }
  }

  if (!current) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-3xl border border-dashed border-border/60 py-16 text-center">
        <p className="text-sm font-medium">All caught up</p>
        <p className="text-xs text-muted-foreground">No open requests left to review.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <p className="text-xs text-muted-foreground">
        {queue.length} open request{queue.length === 1 ? "" : "s"} left
      </p>
      <div className="relative h-72 w-full max-w-sm">
        {stack.map((ticket, index) => (
          <div
            key={ticket.id}
            className="absolute inset-0 rounded-3xl border border-border/60 bg-card shadow-sm"
            style={{ transform: `scale(${1 - (index + 1) * 0.04}) translateY(${(index + 1) * 10}px)` }}
          />
        ))}
        <motion.div
          key={current.id}
          drag={exitDirection === null ? "x" : false}
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.6}
          onDragEnd={handleDragEnd}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={
            exitDirection === null
              ? { x: 0, opacity: 1, rotate: 0, scale: 1 }
              : { x: exitDirection * FLY_OUT_DISTANCE, opacity: 0, rotate: exitDirection * 20 }
          }
          onAnimationComplete={() => {
            if (exitDirection !== null) {
              void finishExit();
            }
          }}
          className="absolute inset-0 z-10 flex cursor-grab flex-col justify-between rounded-3xl border border-border/60 bg-card p-6 shadow-lg active:cursor-grabbing"
        >
          <div>
            <p className="text-xs font-medium text-muted-foreground">Requested by {current.author}</p>
            <h2 className="mt-2 text-xl leading-snug font-semibold">{current.content}</h2>
          </div>
          <p className="text-xs text-muted-foreground">
            {new Date(current.created_at).toLocaleDateString()}
          </p>
        </motion.div>
      </div>
      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={() => startExit(-1)} disabled={isBusy || exitDirection !== null}>
          ❌ Not possible
        </Button>
        <Button variant="secondary" onClick={() => startExit(0)} disabled={isBusy || exitDirection !== null}>
          ⏭ Later
        </Button>
        <Button onClick={() => startExit(1)} disabled={isBusy || exitDirection !== null}>
          ✅ Done
        </Button>
      </div>
    </div>
  );
}
