# Role subagents

One subagent per seat. Each reviews a diff from its seat's perspective and posts
findings. They exist because a solo operator reads a diff once, from one angle;
a subagent reads it from the angle its seat is responsible for.

**They advise; they never approve.** Per G6, AI proposes and a human seat
disposes. Subagent output is input to a human reviewer. Track how often each
seat's findings are accepted — a subagent ignored 95% of the time is
miscalibrated and should be fixed or retired, not left as decoration.
