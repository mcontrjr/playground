import { createEvents, EventAttributes } from "ics";
import { WEDDING } from "./config";

export function generateIcs(): string {
  const start = new Date(WEDDING.dateISO);
  const end   = new Date(start.getTime() + 4 * 60 * 60 * 1000);

  const toArr = (d: Date): [number,number,number,number,number] =>
    [d.getFullYear(), d.getMonth()+1, d.getDate(), d.getHours(), d.getMinutes()];

  const event: EventAttributes = {
    start:       toArr(start),
    end:         toArr(end),
    title:       `${WEDDING.couple} Wedding`,
    location:    WEDDING.address,
    description: `We can't wait to celebrate with you!`,
    status:      "CONFIRMED",
    busyStatus:  "BUSY",
  };

  const { error, value } = createEvents([event]);
  if (error || !value) throw new Error("ICS generation failed");
  return value;
}
