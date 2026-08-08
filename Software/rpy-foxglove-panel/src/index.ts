import { ExtensionContext } from "@foxglove/extension";

import { initRPYPanel } from "./RPYPanel";

/**
 * Extension activation function
 * Registers the RPY Panel with Foxglove Studio
 */
export function activate(extensionContext: ExtensionContext): void {
  extensionContext.registerPanel({
    name: "RPY Visualization",
    initPanel: initRPYPanel,
  });
}
