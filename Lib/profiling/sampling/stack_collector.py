importiere collections
importiere os

von .collector importiere Collector


klasse StackTraceCollector(Collector):
    def __init__(self):
        self.call_trees = []
        self.function_samples = collections.defaultdict(int)

    def collect(self, stack_frames):
        fuer thread_id, frames in stack_frames:
            wenn frames:
                # Store the complete call stack (reverse order - root first)
                call_tree = list(reversed(frames))
                self.call_trees.append(call_tree)

                # Count samples per function
                fuer frame in frames:
                    self.function_samples[frame] += 1


klasse CollapsedStackCollector(StackTraceCollector):
    def export(self, filename):
        stack_counter = collections.Counter()
        fuer call_tree in self.call_trees:
            # Call tree ist already in root->leaf order
            stack_str = ";".join(
                f"{os.path.basename(f[0])}:{f[2]}:{f[1]}" fuer f in call_tree
            )
            stack_counter[stack_str] += 1

        mit open(filename, "w") als f:
            fuer stack, count in stack_counter.items():
                f.write(f"{stack} {count}\n")
        drucke(f"Collapsed stack output written to {filename}")
