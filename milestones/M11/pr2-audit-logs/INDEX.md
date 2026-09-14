# M11 PR 2's 39 plant CI logs and the control run's, one file per `quality-gate` run id

Each file is `gh run view <id> --log` as fetched for `milestones/M11/pr2-deletability-audit.md`, copied byte for byte (ADR-080 amendment 3) except where `[split]` breaks a 12-digit run `tests/test_no_account_identifiers.py` reads as an account ID: three runs in two logs, a runner temp-dir UUID tail and a pytest-truncated all-zeros commit printed twice; deleting `[split]` restores the fetched bytes, whose sha256 is the last column. The control run, on the unmutated head `2465b11`, is the first row (added at ADR-080 amendment 4).

| plant | run id | plant commit | what it removed or weakened | reading | `[split]` | sha256 of the fetched log |
|---|---|---|---|---|---|---|
| CONTROL | [34778857665](34778857665.log) | 2465b11 | nothing: the audited head | 5133 passed, 9 skipped, `check: PASS` | 0 | `f8891e884ecd682e57de22e74fd91397d7a3061b8bdb5c4f153adb81afac6c26` |
| W01 | [34778295404](34778295404.log) | 2e5825ba3fda | writer: the no-key refusal removed | SILENT | 0 | `a6bf64af0b01b369bbfa313c704fe4ec2c938f04765b084d999fa77434fd7035` |
| W02 | [34778311852](34778311852.log) | a6397b923e43 | writer: the 32-byte key floor lowered to 1 | CAUGHT | 0 | `da8029b3a4f82f4e22d77ef1a5727aff5e0bdaaf35fb2dae61ceac18807c82c8` |
| W03 | [34778326365](34778326365.log) | 77bb08668bd9 | writer: an existing --out no longer refused before writing | SILENT | 0 | `362354f5caf6815d2a6caa2c98037683e1d7353ed50a3c35cb3b9c4f88a88aad` |
| W04 | [34778338511](34778338511.log) | 6766685c514d | writer: owner.seat defaults to the pinned seat when missing | CAUGHT | 0 | `40ef1b68393a86fb4ad53ab3cd42749cc8d21997b7f21e4ddfbee428db83640c` |
| W05 | [34778354266](34778354266.log) | a50338f71a21 | writer: owner.oncall defaults when missing | CAUGHT | 0 | `9e31fbcbf0dca727398cf414e4231ce0bc1f10d2f8cccdbb61f3e6cf193ea77a` |
| W06 | [34778369587](34778369587.log) | b7ebc1e5b1af | writer: max_gap_s defaults to 4.0 when missing | CAUGHT | 0 | `372aefb121c8682548219a228073c78b28fa1c9f5d614f3ff481faa9cb25e84e` |
| W07 | [34778381126](34778381126.log) | 21bb845422bd | writer: a tier with no window defaults to 86400 s | CAUGHT | 0 | `f26f93ae57f501ccf56448c3b59ca15916246b3edfbe885085085c0ab73d3191` |
| W08 | [34778398659](34778398659.log) | cc8b2506f6f8 | writer: an event with no caption source defaults to a conventional path | SILENT | 0 | `54809c4891b5f3cd47e2be063e79d7b5b15e187dc5678db78df9720144bba888` |
| W30 | [34778411892](34778411892.log) | 74d528fc7c94 | writer: a rule other than max-gap no longer refused | CAUGHT | 0 | `59a3908a1d3931ff332aafd17e03a7ad76a0b7fd6e1ea382dbf93b354e9bcc49` |
| W31 | [34778425312](34778425312.log) | d5cf65ab63df | writer: max_gap_s type and sign no longer checked | CAUGHT | 0 | `5996efd01dbb0e483339a69dbd2d985bef00735a10d00c307bcd3edebf550abf` |
| W09 | [34778440836](34778440836.log) | a85065da20e8 | writer: max-gap strict > weakened to >= | CAUGHT | 0 | `60cb7797779033099a465b32266253fd16fa258d5a844435703ea1237c8687cd` |
| W10 | [34778453299](34778453299.log) | 990e79ba560a | writer: the gap computed one millisecond short | CAUGHT | 0 | `f5c35e9af916ed3b18a430aee26890848222ac01c4d0c78e7bbce3fcd0c53058` |
| W11 | [34778467613](34778467613.log) | c75012868030 | writer: decision always GO | CAUGHT | 0 | `df64a0034e853b96cab403de5c1fff7c4be8dedeb863e0d04798ce96effb6266` |
| W12 | [34778481596](34778481596.log) | 1a7794b6115a | writer: a NO-GO names no owner | CAUGHT | 0 | `559318068b19a477861efb1d4a22f8f89ad14064966ff8c201cb17c75b9a96f6` |
| W13 | [34778494118](34778494118.log) | c01080350a6a | writer: fix_by ignores the tier's window (always 86400 s) | CAUGHT | 0 | `736af1cd6886acb5731c13bbd363319f15fc3245465c386be8c20315d97bd405` |
| W23 | [34778508538](34778508538.log) | cc1a41b7f074 | writer: a cue with no id no longer refused | SILENT | 0 | `1c86ffc9abd0532e63a530cab01a329b9323ed227ce607e6ef149f356349f599` |
| W24 | [34778521560](34778521560.log) | e80ae862714c | writer: timestamps without an hour field no longer read | CAUGHT | 0 | `4f4bb6757983cf5357a8006e739f6bb294543a24da731fdcda8a3c807b405e0d` |
| W28 | [34778533524](34778533524.log) | ec6d25c24af0 | writer: a cue ending before it starts no longer refused | CAUGHT | 0 | `3ed40709b1e8fbfaeea0ad01907adfe491c15313731a51554000a532762e7215` |
| W29 | [34778550408](34778550408.log) | 1e2539658866 | writer: a duplicate cue id no longer refused | CAUGHT | 0 | `7c66af8c84e77ce39737b03edcbdf050fa5797baa4592d3b4a4d201a2b56f074` |
| W14 | [34778563038](34778563038.log) | 052c923f09e5 | writer: schema validation before writing removed | CAUGHT | 0 | `4710f81034095303962779a4c5476ebf15eabc1cc0bb8acf589fd03f3082c4f2` |
| W22 | [34778574570](34778574570.log) | f753e21e77d7 | writer: tree_clean always true | CAUGHT | 0 | `37208f87817dcfa3be40a3b6af8def806a901cc4f70aabc98bdff8e8543e5c1f` |
| W35 | [34778590354](34778590354.log) | b9db05a449bd | writer: the commit recorded is not HEAD | CAUGHT | 2 | `8b53fae3a4d14d2d8086341357aeef30aee6a33ca3c7b8e91ecd76f74de16d6f` |
| W36 | [34778602211](34778602211.log) | 20cf0845b219 | writer: a directory that is not a git repository no longer refused | CAUGHT | 0 | `2f5b989d8f165ad76bb766d339732c5e4e4467233bb529e19529a8fdc847ea49` |
| W34 | [34778616929](34778616929.log) | aba7b0c661fe | writer: caption_sha256 not over the caption bytes | CAUGHT | 0 | `0d60631a4e717d31bbbf097c89e9fe52e29d49f87db723591aa310197bebb686` |
| W21 | [34778630994](34778630994.log) | 11766c40bd17 | writer: the signature does not cover decision | CAUGHT | 0 | `c06c9db329aeb0125d6395eb67e71cdd013aa6472e550905debd9b3cd4d74ab9` |
| W15 | [34778644790](34778644790.log) | 16832ac3061e | writer: the prior's signature no longer verified | CAUGHT | 0 | `664b36bfcab285d652507122a43975bdb6b61b4598b87bb9438a6549492a0758` |
| W16 | [34778661206](34778661206.log) | 6c8698ccb002 | writer: a prior for another event or tier no longer refused | CAUGHT | 0 | `abf6e1c83c448a474d1ce3424dcc760747f545454b6fc0a4d3cd90d5e9b0318a` |
| W17 | [34778676543](34778676543.log) | 9dd9ea9f4232 | writer: a GO prior (no findings) no longer refused by its own door | CAUGHT | 0 | `28bf941f652329a9a2a9f5fcdd8bf81440e75df1e16afff3c967236d07139106` |
| W32 | [34778688179](34778688179.log) | 46af50cfea25 | writer: a prior naming another scenario no longer refused | CAUGHT | 1 | `343e6d0eafd6707096ca54e6dc6ac532d7ddc87c5aa21bad9e4dff2d91e5a8ef` |
| W33 | [34778704450](34778704450.log) | eae47a38f4af | writer: a delta recorded as mode full | CAUGHT | 0 | `d1af988cbb76877530ed61d3ba298c013b1fadecdb4d34c1972d13b2bd0daf14` |
| W20 | [34778721144](34778721144.log) | 9e5056d0c7e1 | writer: prior_sha256 over re-serialised JSON, not the prior's bytes | CAUGHT | 0 | `dcf97f2e150e6afb98482f1206ce8cca95fefb46e235dff0e5aca41f14214390` |
| W18 | [34778732273](34778732273.log) | 8ff70195251e | writer: a delta drill always writes GO (F4's defect) | CAUGHT | 0 | `8e29709feca174f89cc12c4bed5025bb4742d79ca4ce678bfb77a61f36ea70ab` |
| W19 | [34778746050](34778746050.log) | f401667e2e55 | writer: a delta writes GO whenever the caption bytes differ from the prior's (ADR-080 decision 2's defect) | CAUGHT | 0 | `b47c2e66f40f0b133b5cfbc78c32f1458b04cf12f4d6fa587fd7ab51984a2e88` |
| W25 | [34778763574](34778763574.log) | 982533d5705e | writer: an unexpected crash exits 1 (NO-GO) not 2 | CAUGHT | 0 | `a954e6edb2cd2b31a3d0174a98c05b31c5ec59a5354e14b49cc007beb248777c` |
| W26 | [34778775866](34778775866.log) | 66cafabf0f2a | writer: --help or a malformed command exits 0 (GO) not 2 | CAUGHT | 0 | `38406dff68049ff66cb6bd41107fef220335da8574f53cf33ded27a329ac5c32` |
| W27 | [34778788504](34778788504.log) | 07710eb8271a | writer: a NO-GO exits 0 | CAUGHT | 0 | `4b66427b187effe333555a600fb9309487e404698348b7ffb7c32cfb39897e8e` |
| I3 | [34778806054](34778806054.log) | c608fc9fe0ec | writer: imports pave.verdict (constraint 1) | CAUGHT | 0 | `0d3ce69d0b31ab501a196f655070ebf7d543a06dda27a51dbc1386ecf7e265e3` |
| R01 | [34778819511](34778819511.log) | 680970d304c1 | read: fix_window_s computed one second long | CAUGHT | 0 | `1a3769ad5833047946a9e0fb24d257143606ffa19891827cec240049aeca61bb` |
| R02 | [34778831696](34778831696.log) | f19f509eccdb | read: a finding's cue order swapped | CAUGHT | 0 | `e508a2c7a42b884eceab6088b2ad328be19ca2fc9b38815840b8758676ca16f6` |
