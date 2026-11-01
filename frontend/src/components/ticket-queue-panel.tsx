import { TicketSwiper } from "@/components/ticket-swiper";
import { getTicketQueue } from "@/lib/admin-api";

export async function TicketQueuePanel() {
  const queue = await getTicketQueue();
  return <TicketSwiper initialQueue={queue} />;
}
